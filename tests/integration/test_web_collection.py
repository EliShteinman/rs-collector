import hashlib
import time
from pathlib import Path

import pytest
from tests.fakes import FakeHostConnector, FakeSshSession, ScriptedShellChannel, cluster_replies

from rs_collector.analysis.repository import AnalysisRepository
from rs_collector.analysis.runner import RedisScopeRunner
from rs_collector.collection.collector import SupportPackageCollector
from rs_collector.concurrency.lock import CollectionLockFactory
from rs_collector.console.io import ConsoleIo, ScriptedConsole
from rs_collector.inventory.models import Inventory
from rs_collector.inventory.repository import InventoryRepository
from rs_collector.jobs.models import JobStatus
from rs_collector.jobs.registry import JobRegistry
from rs_collector.packages.repository import PackageRepository
from rs_collector.remote.cluster_connector import ClusterConnector
from rs_collector.settings.credentials import SshCredentials
from rs_collector.settings.models import AppSettings
from rs_collector.web.application import WebApplication
from rs_collector.web.http import Request
from rs_collector.web.security.access import AccessGuard, OpenAccess
from rs_collector.workflows.analyze import AnalyzeWorkflow
from rs_collector.workflows.collect import CollectWorkflow

pytestmark = pytest.mark.integration

_PAYLOAD = b"support package payload"
_REMOTE_PATH = "/tmp/debuginfo.mup.c1.example.com.tar.gz"
_TIMEOUT_SECONDS = 10


class StaticInventory:
    def __init__(self, inventory: Inventory) -> None:
        self._inventory = inventory

    def load(self) -> Inventory:
        return self._inventory


class FakeContext:
    def __init__(
        self, app_settings: AppSettings, session: FakeSshSession, console: ConsoleIo
    ) -> None:
        self._settings = app_settings
        self._session = session
        self._console = console

    @property
    def settings(self) -> AppSettings:
        return self._settings

    def with_console(self, console: ConsoleIo) -> FakeContext:
        return FakeContext(self._settings, self._session, console)

    def inventory(self) -> InventoryRepository:
        return StaticInventory(
            Inventory.model_validate(
                {
                    "environments": [
                        {
                            "name": "production",
                            "clusters": [
                                {"fqdn": "c1.example.com", "nodes": ["n1.c1.example.com"]}
                            ],
                        }
                    ]
                }
            )
        )

    def packages(self) -> PackageRepository:
        return PackageRepository(self._settings.storage)

    def analyses(self) -> AnalysisRepository:
        return AnalysisRepository(self._settings.storage)

    def collect_workflow(self) -> CollectWorkflow:
        return CollectWorkflow(
            ClusterConnector(FakeHostConnector({"n1.c1.example.com": self._session})),
            SupportPackageCollector(self.packages(), self._settings.remote),
            CollectionLockFactory(self._settings.storage.locks_dir),
            self._settings.remote,
            SshCredentials(ssh_user="admin", ssh_password="secret"),
            self._console,
        )

    def access_guard(self) -> AccessGuard:
        return OpenAccess()

    def analyze_workflow(self) -> AnalyzeWorkflow:
        return AnalyzeWorkflow(
            RedisScopeRunner(self.analyses(), self._settings.analysis, self._settings.storage),
            self._console,
        )


@pytest.fixture
def session(app_settings: AppSettings) -> FakeSshSession:
    digest = hashlib.sha256(_PAYLOAD).hexdigest()
    channel = ScriptedShellChannel(
        cluster_replies(_REMOTE_PATH, len(_PAYLOAD), digest), default_reply="{marker}:0\n"
    )
    built = FakeSshSession(channel)
    built.download_payload = _PAYLOAD
    return built


@pytest.fixture
def application(app_settings: AppSettings, session: FakeSshSession) -> WebApplication:
    for directory in (app_settings.storage.packages_dir, app_settings.storage.locks_dir):
        directory.mkdir(parents=True, exist_ok=True)
    return WebApplication(FakeContext(app_settings, session, ScriptedConsole([])), JobRegistry())


def _collect(application: WebApplication, cluster: str = "c1.example.com") -> str:
    response = application.handle(
        Request.parse("POST", "/collect", body=f"cluster={cluster}".encode())
    )
    assert response.status == 303, response.body
    return response.headers["Location"].rsplit("/", maxsplit=1)[1]


def _wait(application: WebApplication, job_id: str) -> str:
    deadline = time.monotonic() + _TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        body = application.handle(Request.parse("GET", f"/api/jobs/{job_id}")).body.decode()
        if f'"status":"{JobStatus.RUNNING.value}"' not in body:
            return body
        time.sleep(0.05)
    raise AssertionError("the collect job never finished")


def test_a_collection_started_from_the_page_stores_the_package(
    application: WebApplication, app_settings: AppSettings
) -> None:
    finished = _wait(application, _collect(application))

    assert JobStatus.SUCCEEDED.value in finished
    stored = PackageRepository(app_settings.storage).list()
    assert stored[0].archive_path.read_bytes() == _PAYLOAD


def test_the_job_log_follows_the_collection(application: WebApplication) -> None:
    finished = _wait(application, _collect(application))

    assert "Connecting to c1.example.com" in finished
    assert "Collecting the support package through n1.c1.example.com" in finished


def test_an_unknown_cluster_is_reported(application: WebApplication) -> None:
    response = application.handle(
        Request.parse("POST", "/collect", body=b"cluster=nowhere.example.com")
    )

    assert response.status == 404


def test_a_package_collected_from_the_page_can_be_analyzed(
    application: WebApplication, app_settings: AppSettings, analyzer: Path
) -> None:
    _wait(application, _collect(application))
    name = PackageRepository(app_settings.storage).list()[0].name

    response = application.handle(
        Request.parse("POST", "/analyze", body=f"package={name}&depth=quick".encode())
    )

    assert response.status == 303
