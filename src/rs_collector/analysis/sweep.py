from datetime import UTC, datetime

from rs_collector.analysis.models import AnalysisMetadata, AnalysisStatus, StoredAnalysis
from rs_collector.analysis.repository import AnalysisRepository
from rs_collector.background.processes import ProcessSignals
from rs_collector.logging_setup.configurator import LoggerFactory


class InterruptedRuns:
    def __init__(
        self, repository: AnalysisRepository, processes: ProcessSignals | None = None
    ) -> None:
        self._repository = repository
        self._processes = processes or ProcessSignals()
        self._logger = LoggerFactory.for_component("analysis.sweep")

    def mark(self) -> tuple[str, ...]:
        abandoned = tuple(
            analysis for analysis in self._repository.list() if self._is_abandoned(analysis)
        )
        for analysis in abandoned:
            self._repository.save(_interrupted(analysis.metadata))
            self._logger.warning(
                "The analysis %s was still marked as running and its process is gone",
                analysis.name,
            )
        return tuple(analysis.name for analysis in abandoned)

    def _is_abandoned(self, analysis: StoredAnalysis) -> bool:
        metadata = analysis.metadata
        if metadata.status is not AnalysisStatus.RUNNING:
            return False
        return metadata.runner_pid is None or not self._processes.is_alive(metadata.runner_pid)


def _interrupted(metadata: AnalysisMetadata) -> AnalysisMetadata:
    return metadata.finished(AnalysisStatus.INTERRUPTED, datetime.now(UTC), exit_status=None)
