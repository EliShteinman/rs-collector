from collections.abc import Mapping

import pytest

from rs_collector.cli.container import Container
from rs_collector.jobs.registry import JobRegistry
from rs_collector.web.application import WebApplication
from rs_collector.web.console import ConsoleFeatures
from rs_collector.web.controllers.files import FilesController
from rs_collector.web.controllers.pages import PagesController
from rs_collector.web.http import Request, Response
from rs_collector.web.navigation import Navigation, Tool
from rs_collector.web.router import Router

pytestmark = pytest.mark.integration


class WeatherTool:
    TOOL = Tool(name="Weather", path="/weather", summary="Ask the sky")

    def register(self, router: Router) -> None:
        router.add("GET", self.TOOL.path, self.show)

    def show(self, _: Request, __: Mapping[str, str]) -> Response:
        return Response.html("<p>Sunny</p>")


def _features(container: Container) -> ConsoleFeatures:
    return ConsoleFeatures(container, container.settings, JobRegistry())


def _get(application: WebApplication, path: str) -> Response:
    return application.handle(Request.parse("GET", path))


def test_every_console_feature_is_registered(container: Container) -> None:
    application = WebApplication(_features(container).all())

    assert _get(application, "/").status == 200


def test_a_new_feature_needs_nothing_but_itself(container: Container) -> None:
    application = WebApplication((*_features(container).all(), WeatherTool()))

    assert _get(application, "/weather").body == b"<p>Sunny</p>"


def test_a_feature_alone_is_an_application() -> None:
    application = WebApplication((WeatherTool(),))

    assert _get(application, "/weather").status == 200


def test_a_lone_feature_serves_nothing_else() -> None:
    application = WebApplication((WeatherTool(),))

    assert _get(application, "/").status == 404


def test_the_navigation_lists_the_tools(container: Container) -> None:
    assert _features(container).navigation().tools == (PagesController.TOOL, FilesController.TOOL)


def test_the_navigation_is_shown_on_the_console(container: Container) -> None:
    features = _features(container)
    application = WebApplication(features.all(), navigation=features.navigation())

    assert FilesController.TOOL.name in _get(application, "/").body.decode()


def test_the_navigation_is_shown_on_another_tool(container: Container) -> None:
    features = _features(container)
    application = WebApplication(features.all(), navigation=features.navigation())

    assert PagesController.TOOL.name in _get(application, "/analyses/").body.decode()


def test_the_current_tool_is_marked(container: Container) -> None:
    features = _features(container)
    application = WebApplication(features.all(), navigation=features.navigation())

    assert 'class="here"' in _get(application, "/analyses/").body.decode()


def test_the_console_offers_each_tool_as_a_card(container: Container) -> None:
    features = _features(container)
    application = WebApplication(features.all(), navigation=features.navigation())

    assert (
        f'class="tool" href="{FilesController.TOOL.path}"' in _get(application, "/").body.decode()
    )


def test_the_card_of_the_open_page_is_marked(container: Container) -> None:
    features = _features(container)
    application = WebApplication(features.all(), navigation=features.navigation())

    assert 'class="tool here"' in _get(application, "/").body.decode()


def test_a_failure_page_keeps_the_navigation(container: Container) -> None:
    features = _features(container)
    application = WebApplication(features.all(), navigation=features.navigation())

    assert FilesController.TOOL.name in _get(application, "/jobs/nothing").body.decode()


def test_the_databases_route_is_not_swallowed_by_the_file_browser(container: Container) -> None:
    application = WebApplication(_features(container).all())

    assert _get(application, "/analyses/never-ran/databases").status == 404


def test_a_page_without_a_navigation_still_renders() -> None:
    application = WebApplication((WeatherTool(),), navigation=Navigation())

    assert _get(application, "/nothing").status == 404
