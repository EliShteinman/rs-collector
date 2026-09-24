from collections.abc import Mapping

import pytest

from rs_collector.exceptions.web import RouteNotFoundError
from rs_collector.web.http import Request, Response
from rs_collector.web.router import Handler, Router

pytestmark = pytest.mark.unit


def _echo(_: Request, parameters: Mapping[str, str]) -> Response:
    return Response.html(str(dict(parameters)))


@pytest.fixture
def router() -> Router:
    built = Router()
    built.add("GET", "/", _echo)
    built.add("GET", "/jobs/{identifier}", _echo)
    built.add("GET", "/analyses/{path*}", _echo)
    built.add("POST", "/collect", _echo)
    return built


def _request(method: str, path: str) -> Request:
    return Request.parse(method=method, path=path)


def test_the_root_route_is_matched(router: Router) -> None:
    assert router.resolve(_request("GET", "/")).status == 200


def test_a_path_parameter_is_captured(router: Router) -> None:
    body = router.resolve(_request("GET", "/jobs/abc123")).body

    assert b"abc123" in body


def test_a_parameter_does_not_swallow_a_slash(router: Router) -> None:
    with pytest.raises(RouteNotFoundError):
        router.resolve(_request("GET", "/jobs/abc/extra"))


def test_a_greedy_parameter_takes_the_rest_of_the_path(router: Router) -> None:
    body = router.resolve(_request("GET", "/analyses/name/redisscope_html/report.html")).body

    assert b"name/redisscope_html/report.html" in body


def test_a_wrong_method_is_not_matched(router: Router) -> None:
    with pytest.raises(RouteNotFoundError):
        router.resolve(_request("GET", "/collect"))


def test_an_unknown_path_is_reported(router: Router) -> None:
    with pytest.raises(RouteNotFoundError):
        router.resolve(_request("GET", "/nothing"))


def _named(name: str) -> Handler:
    def handler(_: Request, __: Mapping[str, str]) -> Response:
        return Response.html(name)

    return handler


def test_a_narrow_route_wins_over_one_added_before_it_that_catches_everything() -> None:
    router = Router()
    router.add("GET", "/analyses/{path*}", _named("files"))
    router.add("GET", "/analyses/{name}/databases", _named("databases"))

    assert router.resolve(_request("GET", "/analyses/run-1/databases")).body == b"databases"


def test_the_catching_route_still_serves_everything_else() -> None:
    router = Router()
    router.add("GET", "/analyses/{path*}", _named("files"))
    router.add("GET", "/analyses/{name}/databases", _named("databases"))

    assert router.resolve(_request("GET", "/analyses/run-1/report.html")).body == b"files"
