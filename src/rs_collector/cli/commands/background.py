import socket

from rs_collector.cli.container import Container

_EXIT_SUCCESS = 0


class StartCommand:
    def __init__(self, container: Container) -> None:
        self._container = container
        self._console = container.console

    def execute(self) -> int:
        pid = self._container.server_launcher().start()
        self._container.crontab().install(self._container.cron_entries().lines())
        self._console.write(f"The display server runs (PID {pid}): {self._address()}")
        self._console.write("It keeps running after you log out and starts again after a reboot.")
        self._console.write("Old packages and analyses are removed daily.")
        return _EXIT_SUCCESS

    def _address(self) -> str:
        serve = self._container.settings.serve
        return f"http://{socket.gethostname()}:{serve.port}/{serve.share_name}/"


class StopCommand:
    def __init__(self, container: Container) -> None:
        self._container = container
        self._console = container.console

    def execute(self) -> int:
        self._container.crontab().remove()
        pid = self._container.server_launcher().stop()
        if pid is None:
            self._console.write("The display server was not running")
        else:
            self._console.write(f"Stopped the display server (PID {pid})")
        self._console.write("It no longer starts after a reboot, and the daily cleanup is off.")
        return _EXIT_SUCCESS
