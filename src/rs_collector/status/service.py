import shutil

from rs_collector.analysis.repository import AnalysisRepository
from rs_collector.background.crontab import CrontabInstaller
from rs_collector.background.pid_file import PidFile
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
            starts_after_reboot=self._crontab.installed(),
            cleanup_schedule=self._settings.background.cleanup_schedule,
            cleanup_last_run=last.finished_at if last is not None else None,
            removed_last_run=(
                last.removed_packages + last.removed_analyses if last is not None else 0
            ),
            keeps_days=self._settings.retention.max_age_days,
        )

    def _storage(self) -> StorageStatus:
        storage = self._settings.storage
        packages = self._packages.list()
        analyses = self._analyses.list()
        usage = shutil.disk_usage(storage.data_root)
        return StorageStatus(
            data_root=storage.data_root,
            free_bytes=usage.free,
            total_bytes=usage.total,
            packages=len(packages),
            packages_bytes=sum(package.metadata.size_bytes for package in packages),
            analyses=len(analyses),
            pinned=sum(1 for item in (*packages, *analyses) if item.metadata.pinned),
        )
