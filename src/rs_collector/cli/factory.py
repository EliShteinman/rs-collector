from argparse import Namespace
from typing import Protocol

from rs_collector.cli.commands.analyze import AnalyzeCommand
from rs_collector.cli.commands.background import StartCommand, StopCommand
from rs_collector.cli.commands.cleanup import CleanupCommand
from rs_collector.cli.commands.collect import CollectCommand
from rs_collector.cli.commands.listing import ListCommand
from rs_collector.cli.commands.pinning import PinCommand, UnpinCommand
from rs_collector.cli.commands.serving import ServeCommand
from rs_collector.cli.container import Container


class Command(Protocol):
    def execute(self) -> int: ...


class CommandFactory:
    def __init__(self, container: Container) -> None:
        self._container = container
        self._builders = {
            "collect": self._collect,
            "analyze": self._analyze,
            "list": self._list,
            "pin": self._pin,
            "unpin": self._unpin,
            "cleanup": self._cleanup,
            "serve": self._serve,
            "start": self._start,
            "stop": self._stop,
        }

    def create(self, arguments: Namespace) -> Command:
        return self._builders[arguments.command](arguments)

    def _collect(self, arguments: Namespace) -> Command:
        return CollectCommand(self._container, arguments.conn_string)

    def _analyze(self, _: Namespace) -> Command:
        return AnalyzeCommand(self._container)

    def _list(self, _: Namespace) -> Command:
        return ListCommand(self._container)

    def _pin(self, arguments: Namespace) -> Command:
        return PinCommand(self._container, arguments.name)

    def _unpin(self, arguments: Namespace) -> Command:
        return UnpinCommand(self._container, arguments.name)

    def _cleanup(self, arguments: Namespace) -> Command:
        return CleanupCommand(self._container, arguments.dry_run)

    def _serve(self, _: Namespace) -> Command:
        return ServeCommand(self._container)

    def _start(self, _: Namespace) -> Command:
        return StartCommand(self._container)

    def _stop(self, _: Namespace) -> Command:
        return StopCommand(self._container)
