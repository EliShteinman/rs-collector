from pathlib import Path

from rs_collector.analysis.models import StoredAnalysis
from rs_collector.analysis.options import AnalysisOptions
from rs_collector.analysis.runner import RedisScopeRunner
from rs_collector.console.io import ConsoleIo
from rs_collector.logging_setup.configurator import LoggerFactory
from rs_collector.packages.models import StoredPackage

_REPORT_DIRECTORY = "redisscope_html"
_REPORT_FILE = "report.html"


class AnalyzeWorkflow:
    def __init__(self, runner: RedisScopeRunner, console: ConsoleIo) -> None:
        self._runner = runner
        self._console = console
        self._logger = LoggerFactory.for_component("workflow.analyze")

    def run_for(self, package: StoredPackage, options: AnalysisOptions) -> StoredAnalysis:
        self._console.write(f"Analyzing {package.name} ...")
        self._logger.info("Analyzing %s with %s", package.name, options.slug())
        analysis = self._runner.analyze(package, options)
        self._report(analysis)
        return analysis

    def report_path(self, analysis: StoredAnalysis) -> Path | None:
        report = analysis.directory / _REPORT_DIRECTORY / _REPORT_FILE
        return report if report.is_file() else None

    def _report(self, analysis: StoredAnalysis) -> None:
        self._console.write(f"Analysis ready: {analysis.directory}")
        report = self.report_path(analysis)
        if report is not None:
            self._console.write(f"Report: {report}")
