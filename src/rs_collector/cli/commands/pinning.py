from rs_collector.cli.container import Container

_EXIT_SUCCESS = 0


class PinCommand:
    def __init__(self, container: Container, name: str) -> None:
        self._container = container
        self._name = name

    def execute(self) -> int:
        self._container.pins().pin(self._name)
        self._container.console.write(f"{self._name} is kept until it is unpinned")
        return _EXIT_SUCCESS


class UnpinCommand:
    def __init__(self, container: Container, name: str) -> None:
        self._container = container
        self._name = name

    def execute(self) -> int:
        self._container.pins().unpin(self._name)
        self._container.console.write(f"{self._name} follows the retention policy again")
        return _EXIT_SUCCESS
