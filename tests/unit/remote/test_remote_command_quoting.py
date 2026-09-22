import pytest
from tests.fakes import ScriptedShellChannel

from rs_collector.collection.cleanup import RemoteCleanup
from rs_collector.collection.models import RemotePackage
from rs_collector.remote.channel_reader import ChannelReader
from rs_collector.remote.root_shell import RootShell
from rs_collector.runtime.clock import FrozenClock
from rs_collector.settings.models import AppSettings

pytestmark = pytest.mark.unit

_HOSTILE_PATH = "/tmp/debuginfo;touch /tmp/pwned.tar.gz"


@pytest.fixture
def channel() -> ScriptedShellChannel:
    return ScriptedShellChannel({}, default_reply="{marker}:0\n")


@pytest.fixture
def shell(channel: ScriptedShellChannel, app_settings: AppSettings) -> RootShell:
    return RootShell(
        channel=channel,
        reader=ChannelReader(channel, clock=FrozenClock(), poll_interval_seconds=1.0),
        settings=app_settings.remote,
    )


def test_the_removed_path_reaches_the_shell_quoted(
    shell: RootShell, channel: ScriptedShellChannel, app_settings: AppSettings
) -> None:
    package = RemotePackage(path=_HOSTILE_PATH, size_bytes=1, sha256="a" * 64)

    RemoteCleanup(shell, app_settings.remote).remove(package)

    assert channel.sent[0].startswith(f"rm -f '{_HOSTILE_PATH}';")
