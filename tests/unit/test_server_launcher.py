from pathlib import Path

import pytest
from tests.fakes import FakeProcessSignals, FakeProgram, FakeSpawner

from rs_collector.background.launcher import ServerLauncher
from rs_collector.background.pid_file import PidFile
from rs_collector.exceptions.background import ServerStartError, ServerStopError
from rs_collector.runtime.clock import FrozenClock
from rs_collector.settings.models import AppSettings

pytestmark = pytest.mark.unit

_PID = 4242


class Harness:
    def __init__(
        self, tmp_path: Path, settings: AppSettings, processes: FakeProcessSignals
    ) -> None:
        self.processes = processes
        self.spawner = FakeSpawner(_PID)
        self.pid_path = tmp_path / "serve.pid"
        self.launcher = ServerLauncher(
            FakeProgram(),
            PidFile(self.pid_path, processes),
            tmp_path / "serve_console.log",
            settings.background,
            spawner=self.spawner,
            processes=processes,
            clock=FrozenClock(),
        )


@pytest.fixture
def running(tmp_path: Path, app_settings: AppSettings) -> Harness:
    return Harness(tmp_path, app_settings, FakeProcessSignals(alive={_PID}))


@pytest.fixture
def crashing(tmp_path: Path, app_settings: AppSettings) -> Harness:
    return Harness(tmp_path, app_settings, FakeProcessSignals(alive=set()))


def test_start_runs_the_serve_command(running: Harness) -> None:
    running.launcher.start()

    assert running.spawner.spawned == [("/usr/local/bin/rsc", "serve")]


def test_start_records_the_pid(running: Harness) -> None:
    running.launcher.start()

    assert running.pid_path.read_text(encoding="utf-8").strip() == str(_PID)


def test_a_second_start_does_not_launch_again(running: Harness) -> None:
    running.launcher.start()
    running.launcher.start()

    assert len(running.spawner.spawned) == 1


def test_a_server_that_dies_right_away_is_reported(crashing: Harness) -> None:
    with pytest.raises(ServerStartError):
        crashing.launcher.start()


def test_a_server_that_dies_right_away_leaves_no_pid_file(crashing: Harness) -> None:
    with pytest.raises(ServerStartError):
        crashing.launcher.start()

    assert not crashing.pid_path.exists()


def test_stop_terminates_the_server(running: Harness) -> None:
    running.launcher.start()

    running.launcher.stop()

    assert running.processes.terminated == [_PID]


def test_stop_without_a_server_reports_nothing_stopped(crashing: Harness) -> None:
    assert crashing.launcher.stop() is None


def test_a_server_that_ignores_stop_is_reported(tmp_path: Path, app_settings: AppSettings) -> None:
    stubborn = Harness(tmp_path, app_settings, FakeProcessSignals({_PID}, dies_on_terminate=False))
    stubborn.launcher.start()

    with pytest.raises(ServerStopError):
        stubborn.launcher.stop()
