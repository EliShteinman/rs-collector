import pytest

from rs_collector.cli.container import Container
from rs_collector.jobs.registry import JobRegistry
from rs_collector.web.application import WebApplication
from rs_collector.web.http import Request, Response

pytestmark = pytest.mark.integration


@pytest.fixture
def analysis_with_package(container: Container, support_package: object) -> str:
    import shutil
    from pathlib import Path

    directory = container.settings.storage.analyses_dir / "c1__default"
    directory.mkdir(parents=True, exist_ok=True)
    shutil.copytree(support_package, directory / "redisscope_sp", dirs_exist_ok=True)
    metadata = {
        "name": directory.name,
        "package_name": "c1__2026-09-23",
        "cluster_fqdn": "c1.example.com",
        "environment": "production",
        "options": {"bdb_id": None, "depth": "default", "mask": False, "verbose": False},
        "command": ["redisscope", "--sp", "x.tar.gz"],
        "analyzed_at": "2026-09-23T10:00:00Z",
        "status": "succeeded",
        "pinned": False,
    }
    import json

    Path(directory / "analysis.json").write_text(json.dumps(metadata), encoding="utf-8")
    return directory.name


@pytest.fixture
def application(container: Container) -> WebApplication:
    return container.web_application(JobRegistry())


def _get(application: WebApplication, path: str) -> Response:
    return application.handle(Request.parse("GET", path))


def _post(application: WebApplication, path: str, body: str) -> Response:
    return application.handle(Request.parse("POST", path, body=body.encode()))


def test_the_page_lists_the_databases_of_the_package(
    application: WebApplication, analysis_with_package: str
) -> None:
    body = _get(application, f"/analyses/{analysis_with_package}/databases").body.decode()

    assert "orders" in body and "sessions" in body


def test_an_active_active_database_is_marked_on_the_page(
    application: WebApplication, analysis_with_package: str
) -> None:
    body = _get(application, f"/analyses/{analysis_with_package}/databases").body.decode()

    assert "Active-Active" in body


def test_the_logs_of_a_database_are_collected_by_name(
    application: WebApplication, analysis_with_package: str
) -> None:
    body = _post(
        application, "/database-logs", f"analysis={analysis_with_package}&database=orders"
    ).body.decode()

    assert "shard 3" in body and "shard 4" in body


def test_the_table_reports_the_node_and_the_role(
    application: WebApplication, analysis_with_package: str
) -> None:
    body = _post(
        application, "/database-logs", f"analysis={analysis_with_package}&database=orders"
    ).body.decode()

    assert "master" in body and "slave" in body


def test_the_merged_log_can_be_read_in_the_viewer(
    application: WebApplication, analysis_with_package: str
) -> None:
    _post(application, "/database-logs", f"analysis={analysis_with_package}&database=orders")

    response = _get(
        application,
        f"/analyses/{analysis_with_package}/rsc_database_logs/1/shard-3.log",
    )

    assert response.status == 200
    assert b"oldest line of shard 3" in response.body


def test_the_sync_log_is_collected_for_an_active_active_database(
    application: WebApplication, analysis_with_package: str
) -> None:
    body = _post(
        application, "/database-logs", f"analysis={analysis_with_package}&database=sessions"
    ).body.decode()

    assert "sync of database 2" in body


def test_an_unknown_database_is_reported(
    application: WebApplication, analysis_with_package: str
) -> None:
    response = _post(
        application, "/database-logs", f"analysis={analysis_with_package}&database=nothing"
    )

    assert response.status == 404


def test_an_analysis_without_an_extracted_package_says_so(
    application: WebApplication, analysis_with_package: str, container: Container
) -> None:
    import shutil

    shutil.rmtree(container.analyses().get(analysis_with_package).directory / "redisscope_sp")

    response = _get(application, f"/analyses/{analysis_with_package}/databases")

    assert response.status == 404
