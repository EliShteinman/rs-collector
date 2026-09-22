import sys
from typing import Protocol

from rs_collector.runtime.bundle import BundleLocator

_MODULE_FLAG = "-m"
_CLI_MODULE = "rs_collector.cli.app"


class Program(Protocol):
    def argv(self, *arguments: str) -> tuple[str, ...]: ...


class RscProgram:
    def __init__(
        self, locator: BundleLocator | None = None, executable: str = sys.executable
    ) -> None:
        self._locator = locator or BundleLocator()
        self._executable = executable

    def argv(self, *arguments: str) -> tuple[str, ...]:
        if self._locator.is_frozen():
            return (self._executable, *arguments)
        return (self._executable, _MODULE_FLAG, _CLI_MODULE, *arguments)
