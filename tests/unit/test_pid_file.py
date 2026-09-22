import os
import subprocess
import sys
from pathlib import Path

import pytest

from rs_collector.background.pid_file import PidFile

pytestmark = pytest.mark.unit


@pytest.fixture
def pid_path(tmp_path: Path) -> Path:
    return tmp_path / "locks" / "serve.pid"


def test_a_missing_file_means_nothing_runs(pid_path: Path) -> None:
    assert PidFile(pid_path).running_pid() is None


def test_a_running_process_is_found(pid_path: Path) -> None:
    PidFile(pid_path).write(os.getpid())

    assert PidFile(pid_path).running_pid() == os.getpid()


def test_a_finished_process_is_not_running(pid_path: Path) -> None:
    process = subprocess.Popen([sys.executable, "-c", "pass"])
    process.wait()
    PidFile(pid_path).write(process.pid)

    assert PidFile(pid_path).running_pid() is None


def test_unreadable_content_means_nothing_runs(pid_path: Path) -> None:
    pid_path.parent.mkdir(parents=True)
    pid_path.write_text("garbage", encoding="utf-8")

    assert PidFile(pid_path).running_pid() is None


def test_remove_deletes_the_file(pid_path: Path) -> None:
    PidFile(pid_path).write(os.getpid())
    PidFile(pid_path).remove()

    assert not pid_path.exists()
