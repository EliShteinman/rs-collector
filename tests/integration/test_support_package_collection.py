import hashlib

import pytest
from tests.fakes import FakeSshSession, ScriptedShellChannel

from rs_collector.collection.collector import SupportPackageCollector
from rs_collector.exceptions.remote import RemoteCommandError, TransferIntegrityError
from rs_collector.packages.models import StoredPackage
from rs_collector.packages.repository import PackageRepository
from rs_collector.remote.channel_reader import ChannelReader
from rs_collector.remote.cluster_connector import ClusterConnection
from rs_collector.remote.output import MarkerFactory
from rs_collector.remote.root_shell import RootShell
from rs_collector.runtime.clock import FrozenClock
from rs_collector.settings.models import AppSettings

pytestmark = pytest.mark.integration

_PAYLOAD = b"support package payload"
_REMOTE_PATH = "/tmp/debuginfo.mup.c1.example.com.tar.gz"


def _digest() -> str:
    return hashlib.sha256(_PAYLOAD).hexdigest()


def _replies(digest: str = "", size: int = len(_PAYLOAD)) -> dict[str, str]:
    return {
        "id -u": "0\n{marker}:0\n",
        "debug_info": f"Collecting...\nFile {_REMOTE_PATH} is saved.\n{{marker}}:0\n",
        "stat -c": f"{size}\n{{marker}}:0\n",
        "sha256sum": f"{digest or _digest()}  {_REMOTE_PATH}\n{{marker}}:0\n",
        "chmod": "{marker}:0\n",
        "rm -f": "{marker}:0\n",
    }


class StubRootSession:
    def __init__(
        self, connection: ClusterConnection, shell: RootShell, channel: ScriptedShellChannel
    ) -> None:
        self.connection = connection
        self.shell = shell
        self.channel = channel


@pytest.fixture
def cluster_connection(app_settings: AppSettings) -> ClusterConnection:
    from rs_collector.inventory.models import Cluster, Hostname

    cluster = Cluster.model_validate(
        {"fqdn": "c1.example.com", "nodes": ["n1.c1.example.com"], "environment": "production"}
    )
    return ClusterConnection(
        cluster=cluster, host=Hostname(value="n1.c1.example.com"), session=FakeSshSession()
    )


def _session(
    connection: ClusterConnection, app_settings: AppSettings, replies: dict[str, str]
) -> StubRootSession:
    channel = ScriptedShellChannel(replies, default_reply="{marker}:0\n")
    shell = RootShell(
        channel=channel,
        reader=ChannelReader(channel, clock=FrozenClock(), poll_interval_seconds=1.0),
        settings=app_settings.remote,
        markers=MarkerFactory(),
    )
    shell.escalate()
    return StubRootSession(connection, shell, channel)


def _collect(
    connection: ClusterConnection, app_settings: AppSettings, replies: dict[str, str] | None = None
) -> tuple[StoredPackage, StubRootSession]:
    session = _session(connection, app_settings, replies or _replies())
    connection.session.download_payload = _PAYLOAD
    collector = SupportPackageCollector(
        PackageRepository(app_settings.storage), app_settings.remote
    )
    return collector.collect(session), session


def test_collect_stores_the_archive(
    cluster_connection: ClusterConnection, app_settings: AppSettings
) -> None:
    stored, _ = _collect(cluster_connection, app_settings)

    assert stored.archive_path.read_bytes() == _PAYLOAD


def test_collect_records_the_host_it_used(
    cluster_connection: ClusterConnection, app_settings: AppSettings
) -> None:
    stored, _ = _collect(cluster_connection, app_settings)

    assert stored.metadata.collected_from == "n1.c1.example.com"


def test_collect_records_the_checksum(
    cluster_connection: ClusterConnection, app_settings: AppSettings
) -> None:
    stored, _ = _collect(cluster_connection, app_settings)

    assert stored.metadata.sha256 == _digest()


def test_collect_removes_the_package_from_the_cluster(
    cluster_connection: ClusterConnection, app_settings: AppSettings
) -> None:
    _, session = _collect(cluster_connection, app_settings)

    assert any(f"rm -f {_REMOTE_PATH}" in sent for sent in session.channel.sent)


def test_collect_makes_the_package_readable_before_downloading(
    cluster_connection: ClusterConnection, app_settings: AppSettings
) -> None:
    _, session = _collect(cluster_connection, app_settings)

    assert any(f"chmod 0644 {_REMOTE_PATH}" in sent for sent in session.channel.sent)


def test_collect_rejects_a_truncated_download(
    cluster_connection: ClusterConnection, app_settings: AppSettings
) -> None:
    with pytest.raises(TransferIntegrityError):
        _collect(cluster_connection, app_settings, _replies(size=999))


def test_collect_rejects_a_corrupted_download(
    cluster_connection: ClusterConnection, app_settings: AppSettings
) -> None:
    with pytest.raises(TransferIntegrityError):
        _collect(cluster_connection, app_settings, _replies(digest="b" * 64))


def test_collect_cleans_the_cluster_even_when_the_transfer_fails(
    cluster_connection: ClusterConnection, app_settings: AppSettings
) -> None:
    session = _session(cluster_connection, app_settings, _replies(size=999))
    cluster_connection.session.download_payload = _PAYLOAD
    collector = SupportPackageCollector(
        PackageRepository(app_settings.storage), app_settings.remote
    )

    with pytest.raises(TransferIntegrityError):
        collector.collect(session)

    assert any(f"rm -f {_REMOTE_PATH}" in sent for sent in session.channel.sent)


def test_collect_reports_a_failing_debug_info(
    cluster_connection: ClusterConnection, app_settings: AppSettings
) -> None:
    replies = {**_replies(), "debug_info": "ERROR: cluster is down\n{marker}:1\n"}

    with pytest.raises(RemoteCommandError):
        _collect(cluster_connection, app_settings, replies)


def test_a_failed_transfer_leaves_no_package_directory(
    cluster_connection: ClusterConnection, app_settings: AppSettings
) -> None:
    with pytest.raises(TransferIntegrityError):
        _collect(cluster_connection, app_settings, _replies(size=999))

    assert list(app_settings.storage.packages_dir.iterdir()) == []
