import subprocess
from collections.abc import Sequence
from pathlib import Path
from typing import Protocol

from rs_collector.exceptions.processes import ProcessStartError, ProcessTimeoutError
from rs_collector.logging_setup.configurator import LoggerFactory

_ENCODING = "utf-8"


class ProcessRunner(Protocol):
    def run(
        self, command: Sequence[str], cwd: Path, log_path: Path, timeout_seconds: int
    ) -> int: ...


class SubprocessRunner:
    def __init__(self) -> None:
        self._logger = LoggerFactory.for_component("processes")

    def run(self, command: Sequence[str], cwd: Path, log_path: Path, timeout_seconds: int) -> int:
        self._logger.debug("Running %s in %s", " ".join(command), cwd)
        with log_path.open("w", encoding=_ENCODING) as log_file:
            try:
                completed = subprocess.run(
                    list(command),
                    cwd=cwd,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    timeout=timeout_seconds,
                    check=False,
                )
            except subprocess.TimeoutExpired as error:
                raise ProcessTimeoutError(
                    f"{command[0]} did not finish within {timeout_seconds} seconds"
                ) from error
            except OSError as error:
                raise ProcessStartError(f"{command[0]} cannot be executed: {error}") from error
        return completed.returncode
