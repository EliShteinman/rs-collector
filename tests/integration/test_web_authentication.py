from base64 import b64encode

import pytest

from rs_collector.cli.container import Container
from rs_collector.jobs.registry import JobRegistry
from rs_collector.settings.credentials import WebCredentials
from rs_collector.settings.paths import ConfigPaths
from rs_collector.web.application import WebApplication
from rs_collector.web.http import Request, Response
from rs_collector.web.security.access import BasicAccess

pytestmark = pytest.mark.integration

_CHALLENGE_HEADER = "WWW-Authenticate"


@pytest.fixture
def application(container: Container) -> WebApplication:
    credentials = WebCredentials(web_user="ops", web_password="letmein")
    return WebApplication(container, JobRegistry(), BasicAccess(credentials))


def _get(application: WebApplication, path: str, authorization: str | None = None) -> Response:
    headers = {"Authorization": authorization} if authorization is not None else {}
    return application.handle(Request.parse("GET", path, headers=headers))


def _login(user: str = "ops", password: str = "letmein") -> str:
    return "Basic " + b64encode(f"{user}:{password}".encode()).decode()


def test_the_console_is_refused_without_a_login(application: WebApplication) -> None:
    assert _get(application, "/").status == 401


def test_the_refusal_asks_the_browser_for_a_login(application: WebApplication) -> None:
    assert _CHALLENGE_HEADER in _get(application, "/").headers


def test_the_refusal_explains_where_the_login_comes_from(application: WebApplication) -> None:
    assert "RSC_WEB_USER" in _get(application, "/").body.decode()


def test_the_console_opens_with_the_login(application: WebApplication) -> None:
    assert _get(application, "/", _login()).status == 200


def test_a_wrong_password_is_refused(application: WebApplication) -> None:
    assert _get(application, "/", _login(password="guess")).status == 401


def test_the_stylesheet_is_refused_without_a_login(application: WebApplication) -> None:
    assert _get(application, "/static/app.css").status == 401


def test_a_stored_file_is_refused_without_a_login(application: WebApplication) -> None:
    assert _get(application, "/analyses").status == 401


def test_an_unknown_path_is_refused_before_it_is_resolved(application: WebApplication) -> None:
    assert _get(application, "/nothing-here").status == 401


def test_the_open_console_reports_that_it_asks_for_no_login(container: Container) -> None:
    body = _get(WebApplication(container, JobRegistry()), "/").body.decode()

    assert "Open to the network" in body


def test_the_protected_console_names_the_user(
    web_paths: ConfigPaths, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("RSC_WEB_USER", "ops")
    monkeypatch.setenv("RSC_WEB_PASSWORD", "letmein")
    application = WebApplication(Container(paths=web_paths), JobRegistry())

    assert "Asks for a login" in _get(application, "/", _login()).body.decode()
