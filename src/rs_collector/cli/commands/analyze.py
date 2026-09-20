from rs_collector.cli.container import Container

_EXIT_SUCCESS = 0


class AnalyzeCommand:
    def __init__(self, container: Container) -> None:
        self._container = container

    def execute(self) -> int:
        self._container.analyze_workflow().run()
        return _EXIT_SUCCESS
