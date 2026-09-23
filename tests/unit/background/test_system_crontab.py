import subprocess

import pytest
from pytest_mock import MockerFixture

from rs_collector.background.crontab import SystemCrontab
from rs_collector.exceptions.background import CrontabError

pytestmark = pytest.mark.unit


def _completed(returncode: int, stdout: str = "", stderr: str = "") -> object:
    return subprocess.CompletedProcess(["crontab"], returncode, stdout, stderr)


def test_an_empty_crontab_reads_as_nothing(mocker: MockerFixture) -> None:
    mocker.patch("subprocess.run", return_value=_completed(1, stderr="no crontab for alice"))

    assert SystemCrontab().read() == ""


def test_a_refused_crontab_is_reported(mocker: MockerFixture) -> None:
    mocker.patch("subprocess.run", return_value=_completed(1, stderr="not allowed"))

    with pytest.raises(CrontabError):
        SystemCrontab().read()


def test_a_missing_crontab_command_is_reported(mocker: MockerFixture) -> None:
    mocker.patch("subprocess.run", side_effect=FileNotFoundError("crontab"))

    with pytest.raises(CrontabError):
        SystemCrontab().write("")


def test_a_forbidden_crontab_is_reported(mocker: MockerFixture) -> None:
    mocker.patch("subprocess.run", side_effect=PermissionError("not allowed"))

    with pytest.raises(CrontabError):
        SystemCrontab().read()
