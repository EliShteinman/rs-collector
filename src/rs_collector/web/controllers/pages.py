from collections.abc import Mapping, Sequence

from rs_collector.analysis.models import StoredAnalysis
from rs_collector.analysis.outputs import AnalysisOutputs
from rs_collector.jobs.registry import JobRegistry
from rs_collector.web.context import WebContext
from rs_collector.web.http import Request, Response
from rs_collector.web.views import index
from rs_collector.web.views.index import AnalysisLinks

_ANALYSES_PATH = "/analyses/"


class PagesController:
    def __init__(self, container: WebContext, jobs: JobRegistry) -> None:
        self._container = container
        self._jobs = jobs

    def index(self, request: Request, _: Mapping[str, str]) -> Response:
        analyses = self._container.analyses().list()
        return Response.html(
            index.render(
                request.url,
                status=self._container.status().collect(),
                clusters=self._container.inventory().load().clusters,
                packages=self._container.packages().list(),
                analyses=analyses,
                links=self._links(analyses),
                jobs=self._jobs.list(),
            )
        )

    def _links(self, analyses: Sequence[StoredAnalysis]) -> Mapping[str, AnalysisLinks]:
        return {analysis.name: self._links_of(analysis) for analysis in analyses}

    def _links_of(self, analysis: StoredAnalysis) -> AnalysisLinks:
        outputs = AnalysisOutputs(analysis)
        report = outputs.report()
        logs = outputs.raw_logs()
        return AnalysisLinks(
            files=f"{_ANALYSES_PATH}{analysis.name}/",
            report=self._relative(analysis, report),
            raw_logs=self._relative(analysis, logs),
        )

    def _relative(self, analysis: StoredAnalysis, target: object) -> str:
        if target is None:
            return ""
        inside = str(target).removeprefix(str(analysis.directory)).lstrip("/")
        return f"{_ANALYSES_PATH}{analysis.name}/{inside}"
