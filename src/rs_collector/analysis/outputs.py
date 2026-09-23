from pathlib import Path

from rs_collector.analysis.models import StoredAnalysis

_MASKED_REPORT_DIRS = ("redisscope_html_mask",)
_REPORT_DIRS = ("redisscope_html",)
_INDEX_NAMES = ("index.html", "report.html")
_HTML_SUFFIX = ".html"
_RAW_LOGS_DIR = "redisscope_sp"


class AnalysisOutputs:
    def __init__(self, analysis: StoredAnalysis) -> None:
        self._analysis = analysis

    def report(self) -> Path | None:
        for directory in self._report_dirs():
            found = self._entry_file(self._analysis.directory / directory)
            if found is not None:
                return found
        return self._top_level_report()

    def raw_logs(self) -> Path | None:
        logs = self._analysis.directory / _RAW_LOGS_DIR
        return logs if logs.is_dir() else None

    def _report_dirs(self) -> tuple[str, ...]:
        if self._analysis.metadata.options.mask:
            return (*_MASKED_REPORT_DIRS, *_REPORT_DIRS)
        return (*_REPORT_DIRS, *_MASKED_REPORT_DIRS)

    def _entry_file(self, directory: Path) -> Path | None:
        if not directory.is_dir():
            return None
        for name in _INDEX_NAMES:
            candidate = directory / name
            if candidate.is_file():
                return candidate
        pages = sorted(page for page in directory.glob(f"*{_HTML_SUFFIX}") if page.is_file())
        return pages[0] if pages else None

    def _top_level_report(self) -> Path | None:
        pages = sorted(
            page for page in self._analysis.directory.glob(f"*{_HTML_SUFFIX}") if page.is_file()
        )
        return pages[0] if pages else None
