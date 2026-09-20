from rs_collector.analysis.models import StoredAnalysis
from rs_collector.cli.container import Container
from rs_collector.packages.models import StoredPackage

_EXIT_SUCCESS = 0
_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M"
_PIN_MARK = "pinned"
_BYTES_PER_MIB = 1_048_576


class ListCommand:
    def __init__(self, container: Container) -> None:
        self._container = container
        self._console = container.console

    def execute(self) -> int:
        self._write_packages()
        self._write_analyses()
        return _EXIT_SUCCESS

    def _write_packages(self) -> None:
        packages = self._container.packages().list()
        self._console.write(f"Packages ({len(packages)}):")
        for package in packages:
            self._console.write(f"  {self._package_line(package)}")

    def _write_analyses(self) -> None:
        analyses = self._container.analyses().list()
        self._console.write(f"Analyses ({len(analyses)}):")
        for analysis in analyses:
            self._console.write(f"  {self._analysis_line(analysis)}")

    def _package_line(self, package: StoredPackage) -> str:
        metadata = package.metadata
        size = metadata.size_bytes / _BYTES_PER_MIB
        return f"{metadata.name}  {size:.1f} MiB{self._pin(metadata.pinned)}"

    def _analysis_line(self, analysis: StoredAnalysis) -> str:
        metadata = analysis.metadata
        analyzed = metadata.analyzed_at.strftime(_TIMESTAMP_FORMAT)
        return f"{metadata.name}  {metadata.status.value}  {analyzed}{self._pin(metadata.pinned)}"

    def _pin(self, pinned: bool) -> str:
        return f"  [{_PIN_MARK}]" if pinned else ""
