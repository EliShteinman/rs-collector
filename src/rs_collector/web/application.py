from collections.abc import Sequence

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
from rs_collector.logging_setup.configurator import LoggerFactory
from rs_collector.web.feature import WebFeature
from rs_collector.web.http import Request, Response
from rs_collector.web.navigation import Navigation
from rs_collector.web.router import Router
from rs_collector.web.security.access import AccessGuard, OpenAccess
from rs_collector.web.security.challenge import challenge
from rs_collector.web.views import failure

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
_DEFAULT_REALM = "rsc"
_UNEXPECTED = "The server hit an unexpected error. The details are in the rsc log."


class WebApplication:
    def __init__(
        self,
        features: Sequence[WebFeature],
        guard: AccessGuard | None = None,
        realm: str = _DEFAULT_REALM,
        navigation: Navigation | None = None,
    ) -> None:
        self._guard = guard or OpenAccess()
        self._realm = realm
        self._navigation = navigation or Navigation()
        self._router = _routed(features)
        self._logger = LoggerFactory.for_component("web")

    def handle(self, request: Request) -> Response:
        if not self._guard.allows(request):
            return challenge(request, self._realm, self._navigation)
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
            return self._page(request, _FAILED_STATUS, "Something went wrong", _UNEXPECTED)

    def _failure(
        self, request: Request, status: int, heading: str, error: RsCollectorError
    ) -> Response:
        self._logger.warning("%s %s: %s", request.method, request.path, error)
        return self._page(request, status, heading, str(error))

    def _page(self, request: Request, status: int, heading: str, detail: str) -> Response:
        return Response.html(
            failure.render(request.url, heading, detail, self._navigation.here(request.path)),
            status=status,
        )


def _routed(features: Sequence[WebFeature]) -> Router:
    router = Router()
    for feature in features:
        feature.register(router)
    return router
