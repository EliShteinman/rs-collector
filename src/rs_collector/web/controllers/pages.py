from collections.abc import Mapping, Sequence
from typing import ClassVar, Protocol

from rs_collector.analysis.models import StoredAnalysis
from rs_collector.analysis.outputs import AnalysisOutputs
from rs_collector.analysis.repository import AnalysisRepository
from rs_collector.inventory.repository import InventoryRepository
from rs_collector.jobs.registry import JobRegistry
from rs_collector.packages.repository import PackageRepository
from rs_collector.status.service import StatusService
from rs_collector.web.http import Request, Response
from rs_collector.web.navigation import Navigation, Tool
from rs_collector.web.router import Router
from rs_collector.web.views import index
from rs_collector.web.views.index import AnalysisLinks

_ANALYSES_PATH = "/analyses/"
_GET = "GET"
_HOME = "/"


class OverviewContext(Protocol):
    def inventory(self) -> InventoryRepository: ...

    def packages(self) -> PackageRepository: ...

    def analyses(self) -> AnalysisRepository: ...

    def status(self) -> StatusService: ...


class PagesController:
    TOOL: ClassVar[Tool] = Tool(
        name="Collect and analyze",
        path=_HOME,
        summary="Collect a support package from a cluster and run RedisScope on it",
    )

    def __init__(
        self,
        context: OverviewContext,
        jobs: JobRegistry,
        navigation: Navigation | None = None,
    ) -> None:
        self._context = context
        self._jobs = jobs
        self._navigation = navigation or Navigation()

    def register(self, router: Router) -> None:
        router.add(_GET, _HOME, self.index)

    def index(self, request: Request, _: Mapping[str, str]) -> Response:
        analyses = self._context.analyses().list()
        return Response.html(
            index.render(
                request.url,
                status=self._context.status().collect(),
                clusters=self._context.inventory().load().clusters,
                packages=self._context.packages().list(),
                analyses=analyses,
                links=self._links(analyses),
                jobs=self._jobs.list(),
                navigation=self._navigation.here(request.path),
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
            analyzer_log=self._relative(analysis, outputs.analyzer_log()),
            analyzer_logs=self._relative(analysis, outputs.analyzer_log_directory()),
            databases=(f"{_ANALYSES_PATH}{analysis.name}/databases" if logs is not None else ""),
        )

    def _relative(self, analysis: StoredAnalysis, target: object) -> str:
        if target is None:
            return ""
        inside = str(target).removeprefix(str(analysis.directory)).lstrip("/")
        return f"{_ANALYSES_PATH}{analysis.name}/{inside}"
