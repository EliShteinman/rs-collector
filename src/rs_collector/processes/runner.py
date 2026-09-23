import os
import signal
import subprocess
import threading
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Protocol

from rs_collector.exceptions.processes import ProcessStartError, ProcessTimeoutError
from rs_collector.logging_setup.configurator import LoggerFactory

_ENCODING = "utf-8"
_LINE_BUFFERED = 1
_NEWLINE = "\n"

LineReader = Callable[[str], None]


class ProcessRunner(Protocol):
    def run(
        self,
        command: Sequence[str],
        cwd: Path,
        log_path: Path,
        timeout_seconds: int,
        on_line: LineReader | None = None,
    ) -> int: ...


class SubprocessRunner:
    def __init__(self) -> None:
        self._logger = LoggerFactory.for_component("processes")

    def run(
        self,
        command: Sequence[str],
        cwd: Path,
        log_path: Path,
        timeout_seconds: int,
        on_line: LineReader | None = None,
    ) -> int:
        self._logger.debug("Running %s in %s", " ".join(command), cwd)
        process = self._started(command, cwd)
        watchdog = threading.Timer(timeout_seconds, self._terminate, args=(process,))
        watchdog.start()
        try:
            self._forward_output(process, log_path, on_line)
            exit_status = process.wait()
        except BaseException:
            self._terminate(process)
            raise
        finally:
            timed_out = not watchdog.is_alive()
            watchdog.cancel()
        if timed_out:
            raise ProcessTimeoutError(
                f"{command[0]} did not finish within {timeout_seconds} seconds"
            )
        return exit_status

    def _started(self, command: Sequence[str], cwd: Path) -> subprocess.Popen[str]:
        try:
            return subprocess.Popen(
                list(command),
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding=_ENCODING,
                errors="replace",
                bufsize=_LINE_BUFFERED,
                start_new_session=True,
            )
        except OSError as error:
            raise ProcessStartError(f"{command[0]} cannot be executed: {error}") from error

    def _terminate(self, process: subprocess.Popen[str]) -> None:
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        except (ProcessLookupError, PermissionError) as error:
            self._logger.debug("The process %d could not be killed: %s", process.pid, error)

    def _forward_output(
        self, process: subprocess.Popen[str], log_path: Path, on_line: LineReader | None
    ) -> None:
        with log_path.open("w", encoding=_ENCODING) as log_file:
            for line in process.stdout or ():
                log_file.write(line)
                log_file.flush()
                if on_line is not None:
                    on_line(line.rstrip(_NEWLINE))
