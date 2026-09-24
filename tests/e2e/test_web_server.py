import json
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
from base64 import b64encode
from collections.abc import Iterator

import pytest

from rs_collector.cli.container import Container
from rs_collector.jobs.models import JobStatus
from rs_collector.settings.credentials import WebCredentials
from rs_collector.settings.models import ServeSettings
from rs_collector.web.application import WebApplication
from rs_collector.web.security.access import BasicAccess
from rs_collector.web.server import WebServer

pytestmark = pytest.mark.e2e

_TIMEOUT_SECONDS = 10


def _free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def _serve_settings(port: int) -> ServeSettings:
    return ServeSettings(
        host="127.0.0.1",
        port=port,
        base_path="",
        auth_realm="rsc",
        max_inline_bytes=5_242_880,
        max_log_lines=5_000,
        max_jobs=50,
        max_job_lines=2_000,
    )


@pytest.fixture
def base_url(container: Container) -> Iterator[str]:
    server = WebServer(WebApplication(container), _serve_settings(_free_port()))
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


def test_a_large_file_arrives_whole_over_http(base_url: str, container: Container) -> None:
    directory = container.settings.storage.analyses_dir / "demo__default" / "redisscope_all"
    directory.mkdir(parents=True)
    (directory / "cluster_dump.bin").write_bytes(b"y" * 2_000_000)

    with urllib.request.urlopen(
        f"{base_url}/analyses/demo__default/redisscope_all/cluster_dump.bin",
        timeout=_TIMEOUT_SECONDS,
    ) as response:
        assert len(response.read()) == 2_000_000


@pytest.fixture
def protected_url(container: Container) -> Iterator[str]:
    guard = BasicAccess(WebCredentials(web_user="ops", web_password="letmein"))
    server = WebServer(WebApplication(container, guard=guard), _serve_settings(_free_port()))
    with server.running() as port:
        yield f"http://127.0.0.1:{port}"


def test_a_protected_server_asks_for_a_login(protected_url: str) -> None:
    status, _ = _get(f"{protected_url}/")

    assert status == 401


def test_a_protected_server_opens_with_the_login(protected_url: str) -> None:
    encoded = b64encode(b"ops:letmein").decode()
    request = urllib.request.Request(
        f"{protected_url}/", headers={"Authorization": f"Basic {encoded}"}
    )
    with urllib.request.urlopen(request, timeout=_TIMEOUT_SECONDS) as response:
        assert response.status == 200
