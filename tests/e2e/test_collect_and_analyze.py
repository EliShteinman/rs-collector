import hashlib
from pathlib import Path

import pytest
from tests.fakes import FakeHostConnector, FakeSshSession, ScriptedShellChannel

from rs_collector.analysis.prompt import AnalysisOptionsPrompt
from rs_collector.analysis.repository import AnalysisRepository
from rs_collector.analysis.runner import RedisScopeRunner
from rs_collector.collection.collector import SupportPackageCollector
from rs_collector.concurrency.lock import CollectionLockFactory
from rs_collector.console.choice import ChoicePrompt
from rs_collector.console.io import ScriptedConsole
from rs_collector.inventory.repository import YamlInventoryRepository
from rs_collector.packages.models import StoredPackage
from rs_collector.packages.repository import PackageRepository
from rs_collector.remote.channel_reader import ChannelReader
from rs_collector.remote.cluster_connector import ClusterConnector
from rs_collector.selection.interactive import InteractiveClusterSelector
from rs_collector.settings.credentials import SshCredentials
from rs_collector.settings.loader import SettingsLoader
from rs_collector.settings.models import AnalysisSettings, AppSettings
from rs_collector.settings.paths import ConfigPaths
from rs_collector.workflows.analyze import AnalyzeWorkflow
from rs_collector.workflows.collect import CollectWorkflow

pytestmark = pytest.mark.e2e

_PAYLOAD = b"support package payload"
_REMOTE_PATH = "/tmp/debuginfo.mup.c1.example.com.tar.gz"
_FAKE_ANALYZER = """#!/bin/sh
echo "args: $@"
mkdir -p redisscope_html redisscope_sp redisscope_logs
echo "<html>report</html>" > redisscope_html/report.html
"""


def _cluster_replies() -> dict[str, str]:
    digest = hashlib.sha256(_PAYLOAD).hexdigest()
    return {
        "id -u": "0\n{marker}:0\n",
        "debug_info": f"File {_REMOTE_PATH} is saved.\n{{marker}}:0\n",
        "stat -c": f"{len(_PAYLOAD)}\n{{marker}}:0\n",
        "sha256sum": f"{digest}  {_REMOTE_PATH}\n{{marker}}:0\n",
    }


class InstantChannelReader(ChannelReader):
    """Reads without waiting between polls."""


@pytest.fixture
def analyzer(tmp_path: Path) -> Path:
    path = tmp_path / "redisscope"
    path.write_text(_FAKE_ANALYZER, encoding="utf-8")
    path.chmod(0o755)
    return path


@pytest.fixture
def settings(deployment: ConfigPaths) -> AppSettings:
    return SettingsLoader(deployment).load()


class Harness:
    def __init__(self, deployment: ConfigPaths, settings: AppSettings, analyzer: Path) -> None:
        self.console = ScriptedConsole(["", "", ""])
        self.channel = ScriptedShellChannel(_cluster_replies(), default_reply="{marker}:0\n")
        self.session = FakeSshSession(self.channel)
        self.session.download_payload = _PAYLOAD
        self.packages = PackageRepository(settings.storage)
        self.analyses = AnalysisRepository(settings.storage)
        analysis_settings = AnalysisSettings(
            redisscope_binary=analyzer,
            timeout_seconds=settings.analysis.timeout_seconds,
            console_log_name=settings.analysis.console_log_name,
        )
        self.selector = InteractiveClusterSelector(
            YamlInventoryRepository(deployment), ChoicePrompt(self.console)
        )
        self.collect = CollectWorkflow(
            ClusterConnector(FakeHostConnector({"n1.c1.example.com": self.session})),
            SupportPackageCollector(self.packages, settings.remote),
            CollectionLockFactory(settings.storage.locks_dir),
            settings.remote,
            SshCredentials(ssh_user="admin", ssh_password="secret"),
            self.console,
        )
        self.analyze = AnalyzeWorkflow(
            RedisScopeRunner(self.analyses, analysis_settings, settings.storage), self.console
        )

    def run(self) -> StoredPackage:
        package = self.collect.run_for(self.selector.select())
        self.analyze.run_for(package, AnalysisOptionsPrompt(self.console).ask())
        return package


@pytest.fixture
def harness(deployment: ConfigPaths, settings: AppSettings, analyzer: Path) -> Harness:
    return Harness(deployment, settings, analyzer)


def test_the_package_is_stored_locally(harness: Harness) -> None:
    package = harness.run()

    assert package.archive_path.read_bytes() == _PAYLOAD


def test_the_cluster_keeps_no_leftover_package(harness: Harness) -> None:
    harness.run()

    assert any(f"rm -f {_REMOTE_PATH}" in sent for sent in harness.channel.sent)


def test_the_fallback_node_is_recorded(harness: Harness) -> None:
    package = harness.run()

    assert package.metadata.collected_from == "n1.c1.example.com"


def test_the_analysis_runs_right_after_the_collection(harness: Harness) -> None:
    harness.run()

    assert len(harness.analyses.list()) == 1


def test_the_report_lands_in_the_analysis_directory(harness: Harness) -> None:
    harness.run()

    analysis = harness.analyses.list()[0]
    assert (analysis.directory / "redisscope_html" / "report.html").is_file()


def test_the_raw_logs_stay_in_the_analysis_directory(harness: Harness) -> None:
    harness.run()

    analysis = harness.analyses.list()[0]
    assert (analysis.directory / "redisscope_sp").is_dir()


def test_the_analysis_is_named_after_the_package(harness: Harness) -> None:
    package = harness.run()

    assert harness.analyses.list()[0].name == f"{package.name}__default"
