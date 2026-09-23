from collections.abc import Mapping

from rs_collector.jobs.registry import JobRegistry
from rs_collector.web.context import WebContext
from rs_collector.web.http import Request, Response
from rs_collector.web.views import index


class PagesController:
    def __init__(self, container: WebContext, jobs: JobRegistry) -> None:
        self._container = container
        self._jobs = jobs

    def index(self, request: Request, _: Mapping[str, str]) -> Response:
        return Response.html(
            index.render(
                request.url,
                clusters=self._container.inventory().load().clusters,
                packages=self._container.packages().list(),
                analyses=self._container.analyses().list(),
                jobs=self._jobs.list(),
            )
        )
