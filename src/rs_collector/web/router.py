import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass

from rs_collector.exceptions.web import RouteNotFoundError
from rs_collector.web.http import Request, Response

Handler = Callable[[Request, Mapping[str, str]], Response]
_PARAMETER = re.compile(r"\{(?P<name>[a-z_]+)(?P<rest>\*?)\}")
_REST = "*"


@dataclass(frozen=True, slots=True)
class Route:
    method: str
    pattern: re.Pattern[str]
    handler: Handler


class Router:
    def __init__(self) -> None:
        self._narrow: list[Route] = []
        self._catching: list[Route] = []

    def add(self, method: str, path: str, handler: Handler) -> None:
        route = Route(method, _compiled(path), handler)
        if _catches_everything(path):
            self._catching.append(route)
            return
        self._narrow.append(route)

    def resolve(self, request: Request) -> Response:
        for route in (*self._narrow, *self._catching):
            match = route.pattern.fullmatch(request.path)
            if match is not None and route.method == request.method:
                return route.handler(request, match.groupdict())
        raise RouteNotFoundError(f"{request.method} {request.path} does not exist")


def _catches_everything(path: str) -> bool:
    return any(match.group("rest") == _REST for match in _PARAMETER.finditer(path))


def _compiled(path: str) -> re.Pattern[str]:
    expression = ""
    position = 0
    for match in _PARAMETER.finditer(path):
        expression += re.escape(path[position : match.start()])
        suffix = ".*" if match.group("rest") else "[^/]+"
        expression += f"(?P<{match.group('name')}>{suffix})"
        position = match.end()
    return re.compile(expression + re.escape(path[position:]))
