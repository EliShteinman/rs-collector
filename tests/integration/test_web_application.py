import gzip
import time
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from rs_collector.analysis.outputs import AnalysisOutputs
from rs_collector.cli.container import Container
from rs_collector.jobs.models import JobStatus
from rs_collector.jobs.registry import JobRegistry
from rs_collector.web.application import WebApplication
from rs_collector.web.http import Request, Response

pytestmark = pytest.mark.integration

_TIMEOUT_SECONDS = 10


@pytest.fixture
def application(container: Container) -> WebApplication:
    return container.web_application(JobRegistry())


def _get(application: WebApplication, path: str, query: str = "") -> Response:
    return application.handle(Request.parse("GET", path, query_string=query))


def _post(application: WebApplication, path: str, body: str) -> Response:
    return application.handle(Request.parse("POST", path, body=body.encode("utf-8")))


def _wait_for_job(application: WebApplication, job_url: str) -> Response:
    deadline = time.monotonic() + _TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        response = _get(application, job_url.replace("/jobs/", "/api/jobs/"))
        if f'"status":"{JobStatus.RUNNING.value}"' not in response.body.decode():
            return response
        time.sleep(0.05)
    raise AssertionError("the job never finished")


def test_the_main_page_offers_the_configured_cluster(application: WebApplication) -> None:
    body = _get(application, "/").body.decode()

    assert 'value="c1.example.com"' in body


def test_the_main_page_offers_a_stored_package(application: WebApplication, package: str) -> None:
    body = _get(application, "/").body.decode()

    assert f'value="{package}"' in body


def test_an_analysis_can_be_started_from_the_page(
    application: WebApplication, package: str
) -> None:
    response = _post(application, "/analyze", f"package={package}&depth=default")

    assert response.status == 303
    assert response.headers["Location"].startswith("/jobs/")


def test_the_job_log_reports_the_finished_analysis(
    application: WebApplication, package: str
) -> None:
    job_url = _post(application, "/analyze", f"package={package}&depth=default").headers["Location"]

    finished = _wait_for_job(application, job_url).body.decode()

    assert JobStatus.SUCCEEDED.value in finished
    assert "is ready" in finished


def test_the_finished_job_links_to_the_report(application: WebApplication, package: str) -> None:
    job_url = _post(application, "/analyze", f"package={package}&depth=default").headers["Location"]

    finished = _wait_for_job(application, job_url).body.decode()

    assert "redisscope_html/report.html" in finished


def test_the_report_is_served(application: WebApplication, package: str) -> None:
    job_url = _post(application, "/analyze", f"package={package}&depth=default").headers["Location"]
    _wait_for_job(application, job_url)
    name = _get(application, "/analyses/").body.decode()

    assert "__default" in name


def test_an_unknown_package_is_reported(application: WebApplication) -> None:
    response = _post(application, "/analyze", "package=missing&depth=default")

    assert response.status == 404


def test_a_path_outside_the_analyses_directory_is_refused(application: WebApplication) -> None:
    response = _get(application, "/analyses/../../../etc/passwd")

    assert response.status == 404


def test_an_unknown_page_is_reported(application: WebApplication) -> None:
    assert _get(application, "/nothing").status == 404


def test_the_stylesheet_is_served(application: WebApplication) -> None:
    response = _get(application, "/static/app.css")

    assert response.status == 200 and response.content_type.startswith("text/css")


def test_the_page_reports_the_free_disk_space(application: WebApplication) -> None:
    body = _get(application, "/").body.decode()

    assert "GB free" in body


def test_the_page_reports_that_nothing_is_scheduled(application: WebApplication) -> None:
    body = _get(application, "/").body.decode()

    assert "Stays down" in body


def test_a_package_can_be_kept_from_the_page(
    application: WebApplication, container: Container, package: str
) -> None:
    response = _post(application, "/keep", f"name={package}")

    assert response.status == 303
    assert container.packages().get(package).metadata.pinned


def test_a_kept_package_can_be_released(
    application: WebApplication, container: Container, package: str
) -> None:
    _post(application, "/keep", f"name={package}")

    _post(application, "/release", f"name={package}")

    assert not container.packages().get(package).metadata.pinned


def test_a_kept_package_is_marked_on_the_page(application: WebApplication, package: str) -> None:
    _post(application, "/keep", f"name={package}")

    assert "kept" in _get(application, "/").body.decode()


def test_keeping_an_unknown_name_is_reported(application: WebApplication) -> None:
    assert _post(application, "/keep", "name=missing").status == 404


def test_the_bundled_font_is_served(application: WebApplication) -> None:
    response = _get(application, "/static/fonts/plex-sans.woff2")

    assert response.status == 200
    assert response.content_type == "font/woff2"
    assert response.body[:4] == b"wOF2"


def test_an_unknown_font_is_refused(application: WebApplication) -> None:
    assert _get(application, "/static/fonts/../../etc/passwd").status == 404


def test_an_unexpected_error_still_answers_the_browser(
    application: WebApplication, mocker: MockerFixture
) -> None:
    mocker.patch(
        "rs_collector.status.service.StatusService.collect",
        side_effect=RuntimeError("something nobody expected"),
    )

    response = _get(application, "/")

    assert response.status == 500
    assert "unexpected error" in response.body.decode()


def _analysis_directory(container: Container, name: str = "demo__default") -> Path:
    directory = container.settings.storage.analyses_dir / name
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def test_the_raw_logs_of_a_package_can_be_browsed(
    application: WebApplication, container: Container
) -> None:
    logs = _analysis_directory(container) / "redisscope_sp" / "node1"
    logs.mkdir(parents=True)
    (logs / "redis-server.log").write_text("started\n", encoding="utf-8")

    body = _get(application, "/analyses/demo__default/redisscope_sp/node1/").body.decode()

    assert "redis-server.log" in body


def test_a_raw_log_is_shown_in_the_browser(
    application: WebApplication, container: Container
) -> None:
    logs = _analysis_directory(container) / "redisscope_sp"
    logs.mkdir(parents=True)
    (logs / "redis-server.log").write_text("the last line\n", encoding="utf-8")

    response = _get(application, "/analyses/demo__default/redisscope_sp/redis-server.log")

    assert response.content_type.startswith("text/html")
    assert b"the last line" in response.body


def test_a_rotated_log_is_unpacked_for_the_browser(
    application: WebApplication, container: Container
) -> None:
    logs = _analysis_directory(container) / "redisscope_sp"
    logs.mkdir(parents=True)
    (logs / "redis-server.log.1.gz").write_bytes(gzip.compress(b"an older line\n"))

    response = _get(application, "/analyses/demo__default/redisscope_sp/redis-server.log.1.gz")

    assert response.content_type.startswith("text/html")
    assert b"an older line" in response.body


def test_the_listing_shows_sizes_and_dates(
    application: WebApplication, container: Container
) -> None:
    directory = _analysis_directory(container)
    (directory / "redisscope_attributes.txt").write_bytes(b"x" * 4036)

    body = _get(application, "/analyses/demo__default/").body.decode()

    assert "3.9 KB" in body


def test_the_console_links_to_the_report_the_analyzer_wrote(
    application: WebApplication, container: Container, package: str
) -> None:
    job_url = _post(application, "/analyze", f"package={package}&depth=default").headers["Location"]
    _wait_for_job(application, job_url)
    directory = container.analyses().list()[0].directory
    (directory / "redisscope_html").mkdir(exist_ok=True)
    (directory / "redisscope_html" / "index.html").write_text("<html></html>", encoding="utf-8")

    body = _get(application, "/").body.decode()

    assert "redisscope_html/index.html" in body


def test_the_console_links_to_the_raw_logs(
    application: WebApplication, container: Container, package: str
) -> None:
    job_url = _post(application, "/analyze", f"package={package}&depth=default").headers["Location"]
    _wait_for_job(application, job_url)
    (container.analyses().list()[0].directory / "redisscope_sp").mkdir(exist_ok=True)

    body = _get(application, "/").body.decode()

    assert "Raw logs" in body and "redisscope_sp" in body


def test_every_analysis_can_be_browsed_even_without_a_report(
    application: WebApplication, package: str
) -> None:
    job_url = _post(application, "/analyze", f"package={package}&depth=default").headers["Location"]
    _wait_for_job(application, job_url)

    assert "All files" in _get(application, "/").body.decode()


def test_a_directory_without_a_trailing_slash_is_redirected(
    application: WebApplication, container: Container
) -> None:
    _analysis_directory(container)

    response = _get(application, "/analyses/demo__default")

    assert response.status == 303
    assert response.headers["Location"] == "/analyses/demo__default/"


def test_entering_the_report_directory_opens_its_page(
    application: WebApplication, container: Container
) -> None:
    pages = _analysis_directory(container) / "redisscope_html"
    pages.mkdir()
    (pages / "index.html").write_text("<html>the report front page</html>", encoding="utf-8")
    (pages / "cluster.html").write_text("<html>another page</html>", encoding="utf-8")

    response = _get(application, "/analyses/demo__default/redisscope_html/")

    assert response.content_type.startswith("text/html")
    assert b"the report front page" in response.body


def test_the_files_of_the_report_directory_can_still_be_listed(
    application: WebApplication, container: Container
) -> None:
    pages = _analysis_directory(container) / "redisscope_html"
    pages.mkdir()
    (pages / "index.html").write_text("<html>the report front page</html>", encoding="utf-8")
    (pages / "cluster.html").write_text("<html>another page</html>", encoding="utf-8")

    body = _get(application, "/analyses/demo__default/redisscope_html/", "list=1").body.decode()

    assert "cluster.html" in body


def _write_log(container: Container, text: str, name: str = "redis-server.log") -> str:
    logs = _analysis_directory(container) / "redisscope_sp"
    logs.mkdir(parents=True, exist_ok=True)
    (logs / name).write_text(text, encoding="utf-8")
    return f"/analyses/demo__default/redisscope_sp/{name}"


def test_a_log_is_shown_with_line_numbers(
    application: WebApplication, container: Container
) -> None:
    url = _write_log(container, "first line\nsecond line\n")

    body = _get(application, url).body.decode()

    assert '<span class="ln">1</span>' in body
    assert '<span class="ln">2</span>' in body


def test_a_failing_line_is_marked_as_an_error(
    application: WebApplication, container: Container
) -> None:
    url = _write_log(container, "2026-09-23 07:41 ERROR could not reach node2\n")

    body = _get(application, url).body.decode()

    assert 'class="logline error"' in body


def test_the_viewer_offers_a_filter_and_the_levels_it_found(
    application: WebApplication, container: Container
) -> None:
    url = _write_log(container, "ERROR broken\nWARNING careful\nplain line\n")

    body = _get(application, url).body.decode()

    assert 'id="log-filter"' in body
    assert 'value="error"' in body and 'value="warning"' in body


def test_a_log_can_still_be_read_as_plain_text(
    application: WebApplication, container: Container
) -> None:
    url = _write_log(container, "just text\n")

    response = _get(application, url, "plain=1")

    assert response.content_type.startswith("text/plain")
    assert response.body == b"just text\n"


def test_a_log_can_be_downloaded_untouched(
    application: WebApplication, container: Container
) -> None:
    url = _write_log(container, "just text\n")

    response = _get(application, url, "raw=1")

    assert response.payload() == b"just text\n"


def test_a_report_is_not_treated_as_a_log(
    application: WebApplication, container: Container
) -> None:
    directory = _analysis_directory(container)
    (directory / "redisscope_healthcheck_report.html").write_text(
        "<html>ok</html>", encoding="utf-8"
    )

    response = _get(application, "/analyses/demo__default/redisscope_healthcheck_report.html")

    assert response.body == b"<html>ok</html>"


def test_a_large_file_is_streamed_instead_of_being_held_in_memory(
    application: WebApplication, container: Container
) -> None:
    directory = _analysis_directory(container) / "redisscope_all"
    directory.mkdir(parents=True)
    big = directory / "cluster_dump.bin"
    big.write_bytes(b"x" * 3_000_000)

    response = _get(application, "/analyses/demo__default/redisscope_all/cluster_dump.bin")

    assert response.body == b""
    assert response.size() == 3_000_000
    assert sum(len(chunk) for chunk in response.chunks(65_536)) == 3_000_000


def test_a_report_stylesheet_is_served_as_a_stylesheet(
    application: WebApplication, container: Container
) -> None:
    pages = _analysis_directory(container) / "redisscope_html"
    pages.mkdir()
    (pages / "index.html").write_text(
        '<html><head><link rel="stylesheet" href="style.css"></head></html>', encoding="utf-8"
    )
    (pages / "style.css").write_text("body { font-family: sans-serif }", encoding="utf-8")

    response = _get(application, "/analyses/demo__default/redisscope_html/style.css")

    assert response.content_type == "text/css; charset=utf-8"
    assert b"font-family" in response.payload()


def test_the_finished_job_links_to_the_report_that_was_written(
    application: WebApplication, container: Container, package: str
) -> None:
    job_url = _post(application, "/analyze", f"package={package}&depth=default").headers["Location"]

    body = _wait_for_job(application, job_url).body.decode()

    written = AnalysisOutputs(container.analyses().list()[0]).report()
    assert written is not None
    assert f"redisscope_html/{written.name}" in body


def test_the_analyzer_output_reaches_the_job_log(application: WebApplication, package: str) -> None:
    job_url = _post(application, "/analyze", f"package={package}&depth=default").headers["Location"]

    finished = _wait_for_job(application, job_url).body.decode()

    assert "RedisScope starting with" in finished
    assert "100% extracted" in finished
