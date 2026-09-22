from pathlib import Path

from rs_collector.background.pid_file import PidFile
from rs_collector.background.processes import DetachedSpawner, ProcessSignals, ProcessSpawner
from rs_collector.background.program import Program
from rs_collector.exceptions.background import ServerStartError, ServerStopError
from rs_collector.logging_setup.configurator import LoggerFactory
from rs_collector.runtime.clock import Clock, SystemClock
from rs_collector.settings.models import BackgroundSettings

_SERVE_COMMAND = "serve"
_POLL_INTERVAL_SECONDS = 0.1


class ServerLauncher:
    def __init__(
        self,
        program: Program,
        pid_file: PidFile,
        console_log: Path,
        settings: BackgroundSettings,
        spawner: ProcessSpawner | None = None,
        processes: ProcessSignals | None = None,
        clock: Clock | None = None,
    ) -> None:
        self._program = program
        self._pid_file = pid_file
        self._console_log = console_log
        self._settings = settings
        self._spawner = spawner or DetachedSpawner()
        self._processes = processes or ProcessSignals()
        self._clock = clock or SystemClock()
        self._logger = LoggerFactory.for_component("background.launcher")

    def start(self) -> int:
        running = self._pid_file.running_pid()
        if running is not None:
            self._logger.info("The display server already runs as PID %d", running)
            return running
        pid = self._spawner.spawn(self._program.argv(_SERVE_COMMAND), self._console_log)
        self._pid_file.write(pid)
        self._confirm_running(pid)
        self._logger.info("Started the display server as PID %d", pid)
        return pid

    def stop(self) -> int | None:
        pid = self._pid_file.running_pid()
        if pid is None:
            self._pid_file.remove()
            self._logger.debug("The display server was not running")
            return None
        self._processes.terminate(pid)
        self._wait_for_exit(pid)
        self._pid_file.remove()
        self._logger.info("Stopped the display server (PID %d)", pid)
        return pid

    def _confirm_running(self, pid: int) -> None:
        self._clock.sleep(self._settings.startup_check_seconds)
        if self._processes.is_alive(pid):
            return
        self._pid_file.remove()
        self._logger.error("The display server exited right after it started")
        raise ServerStartError(
            f"The display server stopped right after it started. See {self._console_log}"
        )

    def _wait_for_exit(self, pid: int) -> None:
        deadline = self._clock.now() + self._settings.stop_timeout_seconds
        while self._processes.is_alive(pid):
            if self._clock.now() >= deadline:
                raise ServerStopError(f"The display server (PID {pid}) did not stop in time")
            self._clock.sleep(_POLL_INTERVAL_SECONDS)
