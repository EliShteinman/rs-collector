import pytest
from tests.fakes import FakeCrontab

from rs_collector.background.crontab import CrontabInstaller

pytestmark = pytest.mark.unit

_FOREIGN = "0 * * * * /home/alice/backup.sh"
_OURS = ("@reboot rsc start # rsc", "30 3 * * * rsc cleanup # rsc")


def test_install_keeps_the_user_lines() -> None:
    crontab = FakeCrontab(f"{_FOREIGN}\n")

    CrontabInstaller(crontab, "# rsc").install(_OURS)

    assert crontab.content.splitlines() == [_FOREIGN, *_OURS]


def test_installing_twice_does_not_duplicate() -> None:
    crontab = FakeCrontab()
    installer = CrontabInstaller(crontab, "# rsc")

    installer.install(_OURS)
    installer.install(_OURS)

    assert crontab.content.splitlines() == list(_OURS)


def test_remove_keeps_the_user_lines() -> None:
    crontab = FakeCrontab("\n".join([_FOREIGN, *_OURS]) + "\n")

    CrontabInstaller(crontab, "# rsc").remove()

    assert crontab.content.splitlines() == [_FOREIGN]


def test_remove_reports_that_nothing_was_installed() -> None:
    assert CrontabInstaller(FakeCrontab(f"{_FOREIGN}\n"), "# rsc").remove() is False
