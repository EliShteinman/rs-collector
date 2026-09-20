from rs_collector.cli.container import Container
from rs_collector.retention.cleaner import CleanupReport

_EXIT_SUCCESS = 0


class CleanupCommand:
    def __init__(self, container: Container, dry_run: bool = False) -> None:
        self._container = container
        self._console = container.console
        self._dry_run = dry_run

    def execute(self) -> int:
        report = self._container.cleaner().clean(dry_run=self._dry_run)
        self._write(report)
        return _EXIT_SUCCESS

    def _write(self, report: CleanupReport) -> None:
        prefix = "Would remove" if report.dry_run else "Removed"
        if report.is_empty:
            self._console.write("Nothing has expired")
            return
        for name in report.removed_packages:
            self._console.write(f"{prefix} package {name}")
        for name in report.removed_analyses:
            self._console.write(f"{prefix} analysis {name}")
