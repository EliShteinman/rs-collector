from rs_collector.cli.container import Container

_EXIT_SUCCESS = 0


class ServeCommand:
    def __init__(self, container: Container) -> None:
        self._container = container

    def execute(self) -> int:
        self._container.interrupted_runs().mark()
        self._container.web_server().serve_forever()
        return _EXIT_SUCCESS
