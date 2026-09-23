from datetime import UTC, datetime

from rs_collector.analysis.command import RedisScopeCommandBuilder
from rs_collector.analysis.models import AnalysisMetadata, AnalysisStatus, StoredAnalysis
from rs_collector.analysis.namer import AnalysisNamer
from rs_collector.analysis.options import AnalysisOptions
from rs_collector.analysis.repository import AnalysisRepository
from rs_collector.exceptions.analysis import (
    AnalysisFailedError,
    AnalysisTimeoutError,
    AnalyzerStartError,
)
from rs_collector.exceptions.processes import ProcessStartError, ProcessTimeoutError
from rs_collector.logging_setup.configurator import LoggerFactory
from rs_collector.packages.models import StoredPackage
from rs_collector.processes.runner import LineReader, ProcessRunner, SubprocessRunner
from rs_collector.settings.models import AnalysisSettings, StorageSettings

_SUCCESS_STATUS = 0


class RedisScopeRunner:
    def __init__(
        self,
        repository: AnalysisRepository,
        settings: AnalysisSettings,
        storage: StorageSettings,
        processes: ProcessRunner | None = None,
        namer: AnalysisNamer | None = None,
        on_line: LineReader | None = None,
    ) -> None:
        self._repository = repository
        self._settings = settings
        self._storage = storage
        self._processes = processes or SubprocessRunner()
        self._namer = namer or AnalysisNamer()
        self._on_line = on_line
        self._builder = RedisScopeCommandBuilder(settings.redisscope_binary)
        self._logger = LoggerFactory.for_component("analysis.runner")

    def analyze(self, package: StoredPackage, options: AnalysisOptions) -> StoredAnalysis:
        started = self._start(package, options)
        try:
            exit_status = self._execute(started)
        except ProcessTimeoutError as error:
            self._finish(started, AnalysisStatus.TIMED_OUT, None)
            self._logger.error("RedisScope timed out: %s", error)
            raise AnalysisTimeoutError(str(error)) from error
        except ProcessStartError as error:
            self._finish(started, AnalysisStatus.FAILED, None)
            self._logger.error("RedisScope could not start: %s", error)
            raise AnalyzerStartError(str(error)) from error
        return self._conclude(started, exit_status)

    def _start(self, package: StoredPackage, options: AnalysisOptions) -> StoredAnalysis:
        name = self._namer.name_for(package.name, options, self._repository.names())
        command = self._builder.build(package.archive_path, options)
        self._logger.info("Analyzing %s as %s", package.name, name)
        return self._repository.create(
            AnalysisMetadata(
                name=name,
                package_name=package.name,
                cluster_fqdn=package.metadata.cluster_fqdn,
                environment=package.metadata.environment,
                options=options,
                command=tuple(command),
                analyzed_at=datetime.now(UTC),
            )
        )

    def _execute(self, started: StoredAnalysis) -> int:
        return self._processes.run(
            command=started.metadata.command,
            cwd=started.directory,
            log_path=started.directory / self._settings.console_log_name,
            timeout_seconds=self._settings.timeout_seconds,
            on_line=self._on_line,
        )

    def _conclude(self, started: StoredAnalysis, exit_status: int) -> StoredAnalysis:
        status = (
            AnalysisStatus.SUCCEEDED if exit_status == _SUCCESS_STATUS else AnalysisStatus.FAILED
        )
        stored = self._finish(started, status, exit_status)
        if status is AnalysisStatus.FAILED:
            self._logger.error("RedisScope exited with status %d", exit_status)
            raise AnalysisFailedError(
                f"RedisScope exited with status {exit_status}. See "
                f"{stored.directory / self._settings.console_log_name}"
            )
        self._logger.info("Analysis %s finished successfully", stored.name)
        return stored

    def _finish(
        self, started: StoredAnalysis, status: AnalysisStatus, exit_status: int | None
    ) -> StoredAnalysis:
        return self._repository.save(
            started.metadata.finished(status, datetime.now(UTC), exit_status)
        )
