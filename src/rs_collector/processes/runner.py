import codecs
import os
import re
import signal
import subprocess
import threading
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Protocol

from rs_collector.exceptions.processes import ProcessStartError, ProcessTimeoutError
from rs_collector.logging_setup.configurator import LoggerFactory
from rs_collector.terminal.escapes import plain

_ENCODING = "utf-8"
_READ_SIZE = 65536
_NEWLINE = "\n"
_CARRIAGE_RETURN = "\r"
_BREAK = re.compile(r"\r\n|\n|\r")

LineReader = Callable[[str, bool], None]


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

    def _started(self, command: Sequence[str], cwd: Path) -> subprocess.Popen[bytes]:
        try:
            return subprocess.Popen(
                list(command),
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
        except OSError as error:
            raise ProcessStartError(f"{command[0]} cannot be executed: {error}") from error

    def _terminate(self, process: subprocess.Popen[bytes]) -> None:
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        except (ProcessLookupError, PermissionError) as error:
            self._logger.debug("The process %d could not be killed: %s", process.pid, error)

    def _forward_output(
        self, process: subprocess.Popen[bytes], log_path: Path, on_line: LineReader | None
    ) -> None:
        output = process.stdout
        if output is None:
            return
        decoder = codecs.getincrementaldecoder(_ENCODING)(errors="replace")
        with log_path.open("w", encoding=_ENCODING, newline="") as log_file:
            pending = ""
            while chunk := os.read(output.fileno(), _READ_SIZE):
                text = decoder.decode(chunk)
                log_file.write(text)
                log_file.flush()
                pending = self._emitted(pending + text, on_line)
            self._emit(pending, overwrite=False, on_line=on_line)

    def _emitted(self, buffered: str, on_line: LineReader | None) -> str:
        while match := _BREAK.search(buffered):
            self._emit(
                buffered[: match.start()],
                overwrite=match.group() == _CARRIAGE_RETURN,
                on_line=on_line,
            )
            buffered = buffered[match.end() :]
        return buffered

    def _emit(self, text: str, overwrite: bool, on_line: LineReader | None) -> None:
        if on_line is None or not text:
            return
        on_line(plain(text), overwrite)
