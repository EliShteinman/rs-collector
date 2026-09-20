from rs_collector.analysis.models import StoredAnalysis
from rs_collector.analysis.prompt import AnalysisOptionsPrompt
from rs_collector.analysis.runner import RedisScopeRunner
from rs_collector.console.io import ConsoleIo
from rs_collector.logging_setup.configurator import LoggerFactory
from rs_collector.packages.models import StoredPackage
from rs_collector.packages.selector import InteractivePackageSelector

_REPORT_DIRECTORY = "redisscope_html"
_REPORT_FILE = "report.html"


class AnalyzeWorkflow:
    def __init__(
        self,
        selector: InteractivePackageSelector,
        options_prompt: AnalysisOptionsPrompt,
        runner: RedisScopeRunner,
        console: ConsoleIo,
    ) -> None:
        self._selector = selector
        self._options_prompt = options_prompt
        self._runner = runner
        self._console = console
        self._logger = LoggerFactory.for_component("workflow.analyze")

    def run(self) -> StoredAnalysis:
        return self.run_for(self._selector.select())

    def run_for(self, package: StoredPackage) -> StoredAnalysis:
        options = self._options_prompt.ask()
        self._console.write(f"Analyzing {package.name} ...")
        analysis = self._runner.analyze(package, options)
        self._report(analysis)
        return analysis

    def _report(self, analysis: StoredAnalysis) -> None:
        self._console.write(f"Analysis ready: {analysis.directory}")
        report = analysis.directory / _REPORT_DIRECTORY / _REPORT_FILE
        if report.is_file():
            self._console.write(f"Report: {report}")
