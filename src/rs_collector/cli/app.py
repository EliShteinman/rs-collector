import sys
from collections.abc import Callable, Sequence

from rs_collector.cli.container import Container
from rs_collector.cli.factory import CommandFactory
from rs_collector.cli.parser import CliParser
from rs_collector.console.io import ConsoleIo, StandardConsole
from rs_collector.exceptions.base import RsCollectorError
from rs_collector.logging_setup.configurator import LoggerFactory
from rs_collector.runtime.privileges import PrivilegeGuard

_EXIT_FAILURE = 1
_EXIT_INTERRUPTED = 130


class CliApplication:
    def __init__(
        self,
        console: ConsoleIo | None = None,
        container_factory: Callable[[ConsoleIo], Container] | None = None,
        guard: PrivilegeGuard | None = None,
    ) -> None:
        self._console = console or StandardConsole()
        self._container_factory = container_factory or self._default_container
        self._guard = guard or PrivilegeGuard()

    def run(self, argv: Sequence[str] | None = None) -> int:
        arguments = CliParser().parse(argv)
        try:
            self._guard.refuse_root()
            container = self._prepared_container()
            return CommandFactory(container).create(arguments).execute()
        except RsCollectorError as error:
            LoggerFactory.for_component("cli").critical("%s failed: %s", arguments.command, error)
            self._console.write(f"Error: {error}")
            return _EXIT_FAILURE
        except KeyboardInterrupt:
            self._console.write("Interrupted")
            return _EXIT_INTERRUPTED

    def _prepared_container(self) -> Container:
        container = self._container_factory(self._console)
        container.configure_logging()
        return container

    def _default_container(self, console: ConsoleIo) -> Container:
        return Container(console=console)


def main(argv: Sequence[str] | None = None) -> int:
    return CliApplication().run(argv)


if __name__ == "__main__":
    sys.exit(main())
