from datetime import UTC, datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from rs_collector.analysis.repository import AnalysisRepository
from rs_collector.logging_setup.configurator import LoggerFactory
from rs_collector.packages.repository import PackageRepository
from rs_collector.retention.policy import RetentionPolicy

if TYPE_CHECKING:
    from rs_collector.retention.history import CleanupHistory


class CleanupReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    removed_packages: tuple[str, ...] = Field(default=())
    removed_analyses: tuple[str, ...] = Field(default=())
    dry_run: bool = Field(default=False)

    @property
    def is_empty(self) -> bool:
        return not self.removed_packages and not self.removed_analyses


class RetentionCleaner:
    def __init__(
        self,
        packages: PackageRepository,
        analyses: AnalysisRepository,
        policy: RetentionPolicy,
        history: CleanupHistory | None = None,
    ) -> None:
        self._packages = packages
        self._analyses = analyses
        self._policy = policy
        self._history = history
        self._logger = LoggerFactory.for_component("retention")

    def clean(self, dry_run: bool = False, now: datetime | None = None) -> CleanupReport:
        moment = now or datetime.now(UTC)
        self._logger.info("Removing items collected before %s", self._policy.cutoff(moment))
        report = self._reported(dry_run, moment)
        if not dry_run and self._history is not None:
            self._history.record(report, finished_at=moment)
        return report

    def _reported(self, dry_run: bool, moment: datetime) -> CleanupReport:
        return CleanupReport(
            removed_packages=self._clean_packages(dry_run, moment),
            removed_analyses=self._clean_analyses(dry_run, moment),
            dry_run=dry_run,
        )

    def _clean_packages(self, dry_run: bool, now: datetime) -> tuple[str, ...]:
        expired = tuple(
            package.name
            for package in self._packages.list()
            if self._policy.package_expired(package, now)
        )
        if not dry_run:
            for name in expired:
                self._packages.delete(name)
        return expired

    def _clean_analyses(self, dry_run: bool, now: datetime) -> tuple[str, ...]:
        expired = tuple(
            analysis.name
            for analysis in self._analyses.list()
            if self._policy.analysis_expired(analysis, now)
        )
        if not dry_run:
            for name in expired:
                self._analyses.delete(name)
        return expired
