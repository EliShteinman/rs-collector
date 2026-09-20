from rs_collector.analysis.repository import AnalysisRepository
from rs_collector.exceptions.storage import (
    AnalysisNotFoundError,
    ArtifactNotFoundError,
    PackageNotFoundError,
)
from rs_collector.logging_setup.configurator import LoggerFactory
from rs_collector.packages.repository import PackageRepository


class PinService:
    def __init__(self, packages: PackageRepository, analyses: AnalysisRepository) -> None:
        self._packages = packages
        self._analyses = analyses
        self._logger = LoggerFactory.for_component("retention.pin")

    def pin(self, name: str) -> None:
        self._set(name, pinned=True)

    def unpin(self, name: str) -> None:
        self._set(name, pinned=False)

    def _set(self, name: str, pinned: bool) -> None:
        if self._try_package(name, pinned) or self._try_analysis(name, pinned):
            self._logger.info("%s is now %s", name, "pinned" if pinned else "unpinned")
            return
        raise ArtifactNotFoundError(f"No package or analysis named '{name}' is stored")

    def _try_package(self, name: str, pinned: bool) -> bool:
        try:
            stored = self._packages.get(name)
        except PackageNotFoundError:
            return False
        self._packages.save(stored.metadata.with_pinned(pinned))
        return True

    def _try_analysis(self, name: str, pinned: bool) -> bool:
        try:
            stored = self._analyses.get(name)
        except AnalysisNotFoundError:
            return False
        self._analyses.save(stored.metadata.with_pinned(pinned))
        return True
