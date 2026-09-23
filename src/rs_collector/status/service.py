import shutil
from pathlib import Path

from rs_collector.analysis.repository import AnalysisRepository
from rs_collector.background.crontab import CrontabInstaller
from rs_collector.background.pid_file import PidFile
from rs_collector.exceptions.background import CrontabError
from rs_collector.logging_setup.configurator import LoggerFactory
from rs_collector.packages.repository import PackageRepository
from rs_collector.retention.history import CleanupHistory
from rs_collector.settings.models import AppSettings
from rs_collector.status.models import ScheduleStatus, ServerStatus, StorageStatus, SystemStatus


class StatusService:
    def __init__(
        self,
        settings: AppSettings,
        pid_file: PidFile,
        crontab: CrontabInstaller,
        history: CleanupHistory,
        packages: PackageRepository,
        analyses: AnalysisRepository,
    ) -> None:
        self._settings = settings
        self._pid_file = pid_file
        self._crontab = crontab
        self._history = history
        self._packages = packages
        self._analyses = analyses
        self._logger = LoggerFactory.for_component("status")

    def collect(self) -> SystemStatus:
        return SystemStatus(
            server=self._server(), schedule=self._schedule(), storage=self._storage()
        )

    def _server(self) -> ServerStatus:
        serve = self._settings.serve
        return ServerStatus(host=serve.host, port=serve.port, pid=self._pid_file.running_pid())

    def _schedule(self) -> ScheduleStatus:
        last = self._history.last()
        return ScheduleStatus(
            starts_after_reboot=self._starts_after_reboot(),
            cleanup_schedule=self._settings.background.cleanup_schedule,
            cleanup_last_run=last.finished_at if last is not None else None,
            removed_last_run=(
                last.removed_packages + last.removed_analyses if last is not None else 0
            ),
            keeps_days=self._settings.retention.max_age_days,
        )

    def _starts_after_reboot(self) -> bool:
        try:
            return self._crontab.installed()
        except CrontabError as error:
            self._logger.warning("The crontab cannot be read: %s", error)
            return False

    def _storage(self) -> StorageStatus:
        storage = self._settings.storage
        packages = self._packages.list()
        analyses = self._analyses.list()
        free_bytes, total_bytes = _free_and_total(storage.data_root)
        return StorageStatus(
            data_root=storage.data_root,
            free_bytes=free_bytes,
            total_bytes=total_bytes,
            packages=len(packages),
            packages_bytes=sum(package.metadata.size_bytes for package in packages),
            analyses=len(analyses),
            pinned=sum(1 for item in (*packages, *analyses) if item.metadata.pinned),
        )


def _free_and_total(path: Path) -> tuple[int, int]:
    for candidate in (path, *path.parents):
        try:
            usage = shutil.disk_usage(candidate)
        except OSError:
            continue
        return usage.free, usage.total
    return 0, 0
