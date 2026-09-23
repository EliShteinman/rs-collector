from collections.abc import Callable, Mapping

from rs_collector.analysis.models import StoredAnalysis
from rs_collector.analysis.options import AnalysisOptions
from rs_collector.analysis.outputs import AnalysisOutputs
from rs_collector.exceptions.selection import ClusterNotFoundError
from rs_collector.inventory.models import Cluster
from rs_collector.jobs.console import JobConsole
from rs_collector.jobs.job import Job
from rs_collector.jobs.models import JobKind
from rs_collector.jobs.registry import JobOutcome, JobRegistry
from rs_collector.packages.models import StoredPackage
from rs_collector.web.context import WebContext
from rs_collector.web.http import Request, Response
from rs_collector.web.requests import AnalyzeRequest, CollectRequest
from rs_collector.web.views import job as job_view

_JOBS_PATH = "/jobs/"
_ANALYSES_PATH = "/analyses/"


class JobsController:
    def __init__(self, container: WebContext, jobs: JobRegistry) -> None:
        self._container = container
        self._jobs = jobs

    def collect(self, request: Request, _: Mapping[str, str]) -> Response:
        cluster = self._cluster(CollectRequest.parse(request.form).cluster)
        started = self._jobs.start(
            JobKind.COLLECT, f"Collect {cluster.name}", self._collect_work(cluster)
        )
        return Response.redirect(request.url(f"{_JOBS_PATH}{started.id}"))

    def analyze(self, request: Request, _: Mapping[str, str]) -> Response:
        asked = AnalyzeRequest.parse(request.form)
        package = self._container.packages().get(asked.package)
        started = self._jobs.start(
            JobKind.ANALYZE,
            f"Analyze {package.name} ({asked.options().slug()})",
            self._analyze_work(package, asked.options()),
        )
        return Response.redirect(request.url(f"{_JOBS_PATH}{started.id}"))

    def show(self, request: Request, parameters: Mapping[str, str]) -> Response:
        job = self._jobs.get(parameters["identifier"])
        return Response.html(job_view.render(request.url, job.view()))

    def log(self, request: Request, parameters: Mapping[str, str]) -> Response:
        job = self._jobs.get(parameters["identifier"])
        return Response.json(job.view(from_line=_offset(request)).model_dump_json())

    def _cluster(self, name: str) -> Cluster:
        cluster = self._container.inventory().load().cluster(name)
        if cluster is None:
            raise ClusterNotFoundError(f"No cluster named '{name}' is configured")
        return cluster

    def _collect_work(self, cluster: Cluster) -> Callable[[Job], JobOutcome]:
        def work(job: Job) -> JobOutcome:
            container = self._container.with_console(JobConsole(job))
            package = container.collect_workflow().run_for(cluster)
            return JobOutcome(f"The package {package.name} is stored")

        return work

    def _analyze_work(
        self, package: StoredPackage, options: AnalysisOptions
    ) -> Callable[[Job], JobOutcome]:
        def work(job: Job) -> JobOutcome:
            container = self._container.with_console(JobConsole(job))
            analysis = container.analyze_workflow().run_for(package, options)
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
