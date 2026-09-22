import os
import signal
import subprocess
from collections.abc import Sequence
from pathlib import Path
from typing import Protocol

_NO_HANG = os.WNOHANG
_EXISTENCE_SIGNAL = 0
_ENCODING = "utf-8"


class ProcessSpawner(Protocol):
    def spawn(self, argv: Sequence[str], log_path: Path) -> int: ...


class DetachedSpawner:
    def spawn(self, argv: Sequence[str], log_path: Path) -> int:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding=_ENCODING) as log_file:
            process = subprocess.Popen(
                list(argv),
                stdin=subprocess.DEVNULL,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                start_new_session=True,
                close_fds=True,
            )
        return process.pid


class ProcessSignals:
    def is_alive(self, pid: int) -> bool:
        self._reap(pid)
        try:
            os.kill(pid, _EXISTENCE_SIGNAL)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        return True

    def terminate(self, pid: int) -> None:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            return

    def _reap(self, pid: int) -> None:
        try:
            os.waitpid(pid, _NO_HANG)
        except ChildProcessError:
            return
