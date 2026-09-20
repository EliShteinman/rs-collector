import pytest
from pydantic import SecretStr
from tests.fakes import ScriptedShellChannel

from rs_collector.exceptions.remote import RemoteCommandError, RootEscalationError
from rs_collector.remote.channel_reader import ChannelReader
from rs_collector.remote.output import MarkerFactory
from rs_collector.remote.root_shell import RootShell
from rs_collector.runtime.clock import FrozenClock
from rs_collector.settings.models import AppSettings

pytestmark = pytest.mark.unit

_ROOT_REPLIES = {"sudo su -": "", "id -u": "0\n{marker}:0\n"}


def _shell(
    channel: ScriptedShellChannel,
    app_settings: AppSettings,
    sudo_password: SecretStr | None = None,
) -> RootShell:
    return RootShell(
        channel=channel,
        reader=ChannelReader(channel, clock=FrozenClock(), poll_interval_seconds=1.0),
        settings=app_settings.remote,
        sudo_password=sudo_password,
        markers=MarkerFactory(),
    )


def test_escalate_sends_sudo_su(app_settings: AppSettings) -> None:
    channel = ScriptedShellChannel(_ROOT_REPLIES, default_reply="{marker}:0\n")

    _shell(channel, app_settings).escalate()

    assert channel.sent[0] == "sudo su -"


def test_escalate_answers_the_password_prompt(app_settings: AppSettings) -> None:
    channel = ScriptedShellChannel(
        {**_ROOT_REPLIES, "sudo su -": "[sudo] password for admin: "},
        default_reply="{marker}:0\n",
    )

    _shell(channel, app_settings, SecretStr("secret")).escalate()

    assert "secret" in channel.sent


def test_escalate_rejects_a_password_prompt_without_a_password(app_settings: AppSettings) -> None:
    channel = ScriptedShellChannel({"sudo su -": "[sudo] password for admin: "})

    with pytest.raises(RootEscalationError):
        _shell(channel, app_settings).escalate()


def test_escalate_rejects_a_shell_that_is_not_root(app_settings: AppSettings) -> None:
    channel = ScriptedShellChannel(
        {"sudo su -": "", "id -u": "id -u\n1000\n{marker}:0\n"}, default_reply="{marker}:0\n"
    )

    with pytest.raises(RootEscalationError):
        _shell(channel, app_settings).escalate()


def test_run_returns_the_command_output(app_settings: AppSettings) -> None:
    channel = ScriptedShellChannel(
        {**_ROOT_REPLIES, "hostname": "node1\n{marker}:0\n"},
        default_reply="{marker}:0\n",
    )
    shell = _shell(channel, app_settings)
    shell.escalate()

    assert shell.run("hostname", timeout_seconds=10).output == "node1"


def test_run_returns_the_exit_status(app_settings: AppSettings) -> None:
    channel = ScriptedShellChannel(
        {**_ROOT_REPLIES, "false": "{marker}:1\n"}, default_reply="{marker}:0\n"
    )
    shell = _shell(channel, app_settings)
    shell.escalate()

    assert shell.run("false", timeout_seconds=10).exit_status == 1


def test_run_checked_rejects_a_failing_command(app_settings: AppSettings) -> None:
    channel = ScriptedShellChannel(
        {**_ROOT_REPLIES, "false": "{marker}:1\n"}, default_reply="{marker}:0\n"
    )
    shell = _shell(channel, app_settings)
    shell.escalate()

    with pytest.raises(RemoteCommandError):
        shell.run_checked("false", timeout_seconds=10)
