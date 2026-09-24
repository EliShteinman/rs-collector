from rs_collector.exceptions.base import RsCollectorError
from rs_collector.exceptions.dblogs import DatabaseNotFoundError, NoLogsForDatabaseError
from rs_collector.exceptions.jobs import JobNotFoundError
from rs_collector.exceptions.selection import ClusterNotFoundError
from rs_collector.exceptions.storage import (
    AnalysisNotFoundError,
    ArtifactNotFoundError,
    PackageNotFoundError,
)
from rs_collector.exceptions.web import BadRequestError, RouteNotFoundError
from rs_collector.jobs.registry import JobRegistry
from rs_collector.logging_setup.configurator import LoggerFactory
from rs_collector.web.context import WebContext
from rs_collector.web.controllers.assets import AssetsController
from rs_collector.web.controllers.databases import DatabasesController
from rs_collector.web.controllers.files import FilesController
from rs_collector.web.controllers.jobs import JobsController
from rs_collector.web.controllers.pages import PagesController
from rs_collector.web.controllers.retention import RetentionController
from rs_collector.web.files.log_lines import LogReader
from rs_collector.web.files.reader import FileReader
from rs_collector.web.http import Request, Response
from rs_collector.web.router import Router
from rs_collector.web.security.access import AccessGuard
from rs_collector.web.security.challenge import challenge
from rs_collector.web.views import failure

_GET = "GET"
_POST = "POST"
_NOT_FOUND = (
    RouteNotFoundError,
    JobNotFoundError,
    ArtifactNotFoundError,
    PackageNotFoundError,
    ClusterNotFoundError,
    AnalysisNotFoundError,
    DatabaseNotFoundError,
    NoLogsForDatabaseError,
)
_NOT_FOUND_STATUS = 404
_BAD_REQUEST_STATUS = 400
_FAILED_STATUS = 500
_UNEXPECTED = "The server hit an unexpected error. The details are in the rsc log."


class WebApplication:
    def __init__(
        self,
        container: WebContext,
        jobs: JobRegistry | None = None,
        guard: AccessGuard | None = None,
    ) -> None:
        self._container = container
        serve = container.settings.serve
        self._jobs = jobs or JobRegistry(serve.max_jobs, serve.max_job_lines)
        self._guard = guard or container.access_guard()
        self._realm = serve.auth_realm
        self._router = self._routes()
        self._logger = LoggerFactory.for_component("web")

    def handle(self, request: Request) -> Response:
        if not self._guard.allows(request):
            return challenge(request, self._realm)
        try:
            return self._router.resolve(request)
        except _NOT_FOUND as error:
            return self._failure(request, _NOT_FOUND_STATUS, "Not found", error)
        except BadRequestError as error:
            return self._failure(request, _BAD_REQUEST_STATUS, "Bad request", error)
        except RsCollectorError as error:
            return self._failure(request, _FAILED_STATUS, "Something went wrong", error)
        except Exception:
            self._logger.exception("%s %s crashed", request.method, request.path)
            return Response.html(
                failure.render(request.url, "Something went wrong", _UNEXPECTED),
                status=_FAILED_STATUS,
            )

    def _routes(self) -> Router:
        pages = PagesController(self._container, self._jobs)
        jobs = JobsController(self._container, self._jobs)
        files = FilesController(
            self._container.settings.storage.analyses_dir,
            FileReader(self._container.settings.serve.max_inline_bytes),
            LogReader(self._container.settings.serve.max_log_lines),
        )
        assets = AssetsController()
        retention = RetentionController(self._container)
        databases = DatabasesController(self._container)
        router = Router()
        router.add(_GET, "/", pages.index)
        router.add(_POST, "/collect", jobs.collect)
        router.add(_POST, "/analyze", jobs.analyze)
        router.add(_POST, "/keep", retention.keep)
        router.add(_POST, "/release", retention.release)
        router.add(_GET, "/jobs/{identifier}", jobs.show)
        router.add(_GET, "/api/jobs/{identifier}", jobs.log)
        router.add(_GET, "/analyses/{name}/databases", databases.show)
        router.add(_POST, "/database-logs", databases.collect)
        router.add(_GET, "/analyses/{path*}", files.serve)
        router.add(_GET, "/analyses", files.serve)
        router.add(_GET, "/static/app.css", assets.stylesheet)
        router.add(_GET, "/static/app.js", assets.javascript)
        router.add(_GET, "/static/fonts/{name}", assets.font)
        return router

    def _failure(
        self, request: Request, status: int, heading: str, error: RsCollectorError
    ) -> Response:
        self._logger.warning("%s %s: %s", request.method, request.path, error)
        return Response.html(failure.render(request.url, heading, str(error)), status=status)
