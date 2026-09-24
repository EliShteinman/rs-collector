from collections.abc import Callable, Mapping
from typing import Protocol

from rs_collector.analysis.models import StoredAnalysis
from rs_collector.analysis.options import AnalysisOptions
from rs_collector.analysis.outputs import AnalysisOutputs
from rs_collector.console.io import ConsoleIo
from rs_collector.exceptions.selection import ClusterNotFoundError
from rs_collector.inventory.models import Cluster
from rs_collector.inventory.repository import InventoryRepository
from rs_collector.jobs.console import JobConsole
from rs_collector.jobs.job import Job
from rs_collector.jobs.models import JobKind
from rs_collector.jobs.registry import JobOutcome, JobRegistry
from rs_collector.packages.models import StoredPackage
from rs_collector.packages.repository import PackageRepository
from rs_collector.web.http import Request, Response
from rs_collector.web.navigation import Navigation
from rs_collector.web.requests import AnalyzeRequest, CollectRequest
from rs_collector.web.router import Router
from rs_collector.web.views import job as job_view
from rs_collector.web.views.log_html import as_html
from rs_collector.workflows.analyze import AnalyzeWorkflow
from rs_collector.workflows.collect import CollectWorkflow

_JOBS_PATH = "/jobs/"
_ANALYSES_PATH = "/analyses/"
_GET = "GET"
_POST = "POST"


class WorkContext(Protocol):
    def with_console(self, console: ConsoleIo) -> WorkContext: ...

    def inventory(self) -> InventoryRepository: ...

    def packages(self) -> PackageRepository: ...

    def collect_workflow(self) -> CollectWorkflow: ...

    def analyze_workflow(self) -> AnalyzeWorkflow: ...


class JobsController:
    def __init__(
        self, context: WorkContext, jobs: JobRegistry, navigation: Navigation | None = None
    ) -> None:
        self._context = context
        self._jobs = jobs
        self._navigation = navigation or Navigation()

    def register(self, router: Router) -> None:
        router.add(_POST, "/collect", self.collect)
        router.add(_POST, "/analyze", self.analyze)
        router.add(_GET, "/jobs/{identifier}", self.show)
        router.add(_GET, "/api/jobs/{identifier}", self.log)

    def collect(self, request: Request, _: Mapping[str, str]) -> Response:
        cluster = self._cluster(CollectRequest.parse(request.form).cluster)
        started = self._jobs.start(
            JobKind.COLLECT, f"Collect {cluster.name}", self._collect_work(cluster)
        )
        return Response.redirect(request.url(f"{_JOBS_PATH}{started.id}"))

    def analyze(self, request: Request, _: Mapping[str, str]) -> Response:
        asked = AnalyzeRequest.parse(request.form)
        package = self._context.packages().get(asked.package)
        started = self._jobs.start(
            JobKind.ANALYZE,
            f"Analyze {package.name} ({asked.options().slug()})",
            self._analyze_work(package, asked.options()),
        )
        return Response.redirect(request.url(f"{_JOBS_PATH}{started.id}"))

    def show(self, request: Request, parameters: Mapping[str, str]) -> Response:
        job = self._jobs.get(parameters["identifier"])
        return Response.html(
            job_view.render(request.url, job.view(), self._navigation.here(request.path))
        )

    def log(self, request: Request, parameters: Mapping[str, str]) -> Response:
        job = self._jobs.get(parameters["identifier"])
        view = job.view(from_line=_offset(request))
        return Response.json(
            view.model_copy(
                update={"lines": tuple(as_html(line) for line in view.lines)}
            ).model_dump_json()
        )

    def _cluster(self, name: str) -> Cluster:
        cluster = self._context.inventory().load().cluster(name)
        if cluster is None:
            raise ClusterNotFoundError(f"No cluster named '{name}' is configured")
        return cluster

    def _collect_work(self, cluster: Cluster) -> Callable[[Job], JobOutcome]:
        def work(job: Job) -> JobOutcome:
            context = self._context.with_console(JobConsole(job))
            package = context.collect_workflow().run_for(cluster)
            return JobOutcome(f"The package {package.name} is stored")

        return work

    def _analyze_work(
        self, package: StoredPackage, options: AnalysisOptions
    ) -> Callable[[Job], JobOutcome]:
        def work(job: Job) -> JobOutcome:
            context = self._context.with_console(JobConsole(job))
            analysis = context.analyze_workflow().run_for(package, options)
            return JobOutcome(f"The analysis {analysis.name} is ready", _report_url(analysis))

        return work


def _report_url(analysis: StoredAnalysis) -> str:
    report = AnalysisOutputs(analysis).report()
    if report is None:
        return f"{_ANALYSES_PATH}{analysis.name}/"
    inside = str(report).removeprefix(str(analysis.directory)).lstrip("/")
    return f"{_ANALYSES_PATH}{analysis.name}/{inside}"


def _offset(request: Request) -> int:
    asked = request.query.get("from", "0")
    return int(asked) if asked.isdigit() else 0
