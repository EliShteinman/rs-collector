from pathlib import Path

import pytest
from tests.fakes import FakeProgram

from rs_collector.background.cron_entries import CronEntries
from rs_collector.settings.models import AppSettings

pytestmark = pytest.mark.unit

_ENVIRONMENT = {
    "RSC_DATA_ROOT": "/mnt/storage/rsc",
    "RSC_CONFIG_DIR": "/etc/rsc/config",
    "RSC_SSH_PASSWORD": "secret",
}


@pytest.fixture
def lines(app_settings: AppSettings) -> tuple[str, ...]:
    entries = CronEntries(FakeProgram(), app_settings.background, _ENVIRONMENT, Path("/home/alice"))
    return entries.lines()


def test_the_server_starts_after_a_reboot(lines: tuple[str, ...]) -> None:
    assert lines[0].startswith("@reboot ") and "/usr/local/bin/rsc start" in lines[0]


def test_the_cleanup_runs_on_its_schedule(lines: tuple[str, ...]) -> None:
    assert lines[1].startswith("30 3 * * * ") and "/usr/local/bin/rsc cleanup" in lines[1]


def test_the_data_root_is_carried_to_cron(lines: tuple[str, ...]) -> None:
    assert "RSC_DATA_ROOT=/mnt/storage/rsc" in lines[0]


def test_secrets_are_not_written_to_the_crontab(lines: tuple[str, ...]) -> None:
    assert all("secret" not in line for line in lines)


def test_cron_runs_in_the_directory_rsc_was_started_from(lines: tuple[str, ...]) -> None:
    assert "cd /home/alice &&" in lines[0]


def test_every_line_carries_the_marker(lines: tuple[str, ...]) -> None:
    assert all(line.endswith("# rsc") for line in lines)


def test_a_percent_sign_is_escaped_for_cron(app_settings: AppSettings) -> None:
    entries = CronEntries(
        FakeProgram(), app_settings.background, {"RSC_DATA_ROOT": "/data/50%"}, Path("/")
    )

    assert "/data/50\\%" in entries.lines()[0]
