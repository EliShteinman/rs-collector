import sys
from pathlib import Path

import pytest
from tests.fakes import FakeProgram

from rs_collector.background.launcher import ServerLauncher
from rs_collector.background.pid_file import PidFile
from rs_collector.background.processes import ProcessSignals
from rs_collector.settings.models import AppSettings

pytestmark = pytest.mark.integration

_SLEEPER = ("-c", "import sys, time; time.sleep(60)")


@pytest.fixture
def launcher(tmp_path: Path, app_settings: AppSettings) -> ServerLauncher:
    program = FakeProgram(sys.executable, *_SLEEPER)
    return ServerLauncher(
        program, PidFile(tmp_path / "serve.pid"), tmp_path / "console.log", app_settings.background
    )


def test_a_started_server_keeps_running(launcher: ServerLauncher) -> None:
    pid = launcher.start()

    assert ProcessSignals().is_alive(pid)
    launcher.stop()


def test_a_stopped_server_is_gone(launcher: ServerLauncher) -> None:
    pid = launcher.start()

    launcher.stop()

    assert not ProcessSignals().is_alive(pid)
