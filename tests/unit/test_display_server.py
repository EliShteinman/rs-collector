from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from rs_collector.exceptions.serve import DisplayServerStartError
from rs_collector.serve.server import DisplayServer, DisplayServerCommandBuilder
from rs_collector.settings.models import AppSettings

pytestmark = pytest.mark.unit


@pytest.fixture
def command(app_settings: AppSettings) -> tuple[str, ...]:
    builder = DisplayServerCommandBuilder(
        app_settings.serve, app_settings.storage, Path("/etc/rsc/config/copyparty.conf")
    )
    return tuple(builder.build())


def test_the_program_name_leads_the_arguments(command: tuple[str, ...]) -> None:
    assert command[0] == "copyparty"


def test_the_configuration_file_is_passed(command: tuple[str, ...]) -> None:
    assert command[1:3] == ("-c", "/etc/rsc/config/copyparty.conf")


def test_the_port_comes_from_the_settings(command: tuple[str, ...]) -> None:
    assert "3923" in command


def test_the_analyses_directory_is_shared_read_only(
    command: tuple[str, ...], app_settings: AppSettings
) -> None:
    assert command[-1] == f"{app_settings.storage.analyses_dir}:/analyses:r"


def test_a_normal_shutdown_is_not_an_error(
    app_settings: AppSettings, mocker: MockerFixture
) -> None:
    mocker.patch("copyparty.__main__.main", side_effect=SystemExit(0))
    server = DisplayServer(app_settings.serve, app_settings.storage, Path("copyparty.conf"))

    server.start()


def test_a_failed_start_is_reported(app_settings: AppSettings, mocker: MockerFixture) -> None:
    mocker.patch("copyparty.__main__.main", side_effect=SystemExit(2))
    server = DisplayServer(app_settings.serve, app_settings.storage, Path("copyparty.conf"))

    with pytest.raises(DisplayServerStartError):
        server.start()
