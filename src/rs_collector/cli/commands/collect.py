from rs_collector.cli.container import Container

_EXIT_SUCCESS = 0
_ANALYZE_QUESTION = "Analyze this package now?"


class CollectCommand:
    def __init__(self, container: Container, connection_string: str | None = None) -> None:
        self._container = container
        self._connection_string = connection_string
        self._console = container.console

    def execute(self) -> int:
        cluster = self._container.cluster_selector(self._connection_string).select()
        package = self._container.collect_workflow().run_for(cluster)
        if self._container.confirm_prompt().ask(_ANALYZE_QUESTION, default=True):
            options = self._container.options_prompt().ask()
            self._container.analyze_workflow().run_for(package, options)
        return _EXIT_SUCCESS
