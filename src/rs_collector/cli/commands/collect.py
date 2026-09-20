from rs_collector.cli.container import Container

_EXIT_SUCCESS = 0


class CollectCommand:
    def __init__(self, container: Container, connection_string: str | None = None) -> None:
        self._container = container
        self._connection_string = connection_string

    def execute(self) -> int:
        self._container.collect_workflow(self._connection_string).run()
        return _EXIT_SUCCESS
