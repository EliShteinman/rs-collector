import json
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Iterator

import pytest

from rs_collector.cli.container import Container
from rs_collector.jobs.models import JobStatus
from rs_collector.settings.models import ServeSettings
from rs_collector.web.application import WebApplication
from rs_collector.web.server import WebServer

pytestmark = pytest.mark.e2e

_TIMEOUT_SECONDS = 10


def _free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


@pytest.fixture
def base_url(container: Container) -> Iterator[str]:
    settings = ServeSettings(
        host="127.0.0.1",
        port=_free_port(),
        base_path="",
        max_inline_bytes=5_242_880,
        max_log_lines=5_000,
    )
    server = WebServer(WebApplication(container), settings)
    with server.running() as port:
        yield f"http://127.0.0.1:{port}"


def _get(url: str) -> tuple[int, str]:
    try:
        with urllib.request.urlopen(url, timeout=_TIMEOUT_SECONDS) as response:
            return response.status, response.read().decode()
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode()


def _post(url: str, fields: dict[str, str]) -> tuple[int, str]:
    body = urllib.parse.urlencode(fields).encode()
    request = urllib.request.Request(url, data=body, method="POST")
    with urllib.request.urlopen(request, timeout=_TIMEOUT_SECONDS) as response:
        return response.status, response.geturl()


def test_the_page_is_served_over_http(base_url: str) -> None:
    status, body = _get(f"{base_url}/")

    assert status == 200
    assert "Collect a support package" in body


def test_an_analysis_runs_and_the_report_is_served(base_url: str, package: str) -> None:
    status, final_url = _post(f"{base_url}/analyze", {"package": package, "depth": "default"})
    assert status == 200

    job_id = final_url.rstrip("/").rsplit("/", maxsplit=1)[1]
    deadline = time.monotonic() + _TIMEOUT_SECONDS
    view: dict[str, object] = {}
    while time.monotonic() < deadline:
        _, payload = _get(f"{base_url}/api/jobs/{job_id}")
        view = json.loads(payload)
        if view["status"] != JobStatus.RUNNING.value:
            break
        time.sleep(0.05)

    assert view["status"] == JobStatus.SUCCEEDED.value
    report_status, report = _get(f"{base_url}{view['report_url']}")
    assert report_status == 200
    assert "the report" in report


def test_a_missing_page_answers_404(base_url: str) -> None:
    status, _ = _get(f"{base_url}/nothing")

    assert status == 404
