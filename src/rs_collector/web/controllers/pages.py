from collections.abc import Mapping, Sequence

from rs_collector.analysis.models import StoredAnalysis
from rs_collector.jobs.registry import JobRegistry
from rs_collector.web.context import WebContext
from rs_collector.web.http import Request, Response
from rs_collector.web.views import index

_ANALYSES_PATH = "/analyses/"
_REPORT_FILE = "redisscope_html/report.html"


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
                reports=self._reports(analyses),
                jobs=self._jobs.list(),
            )
        )

    def _reports(self, analyses: Sequence[StoredAnalysis]) -> Mapping[str, str]:
        return {
            analysis.name: f"{_ANALYSES_PATH}{analysis.name}/{_REPORT_FILE}"
            for analysis in analyses
            if (analysis.directory / _REPORT_FILE).is_file()
        }
