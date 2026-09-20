from pathlib import Path

import pytest

from rs_collector.serve.server import DisplayServerCommandBuilder
from rs_collector.settings.models import AppSettings

pytestmark = pytest.mark.unit


@pytest.fixture
def command(app_settings: AppSettings) -> tuple[str, ...]:
    builder = DisplayServerCommandBuilder(
        app_settings.serve, app_settings.storage, Path("/etc/rsc/config/copyparty.conf")
    )
    return tuple(builder.build())


def test_the_configuration_file_is_passed(command: tuple[str, ...]) -> None:
    assert command[:2] == ("-c", "/etc/rsc/config/copyparty.conf")


def test_the_port_comes_from_the_settings(command: tuple[str, ...]) -> None:
    assert "3923" in command


def test_the_analyses_directory_is_shared_read_only(
    command: tuple[str, ...], app_settings: AppSettings
) -> None:
    assert command[-1] == f"{app_settings.storage.analyses_dir}:/analyses:r"
