from rs_collector.cli.container import Container

_EXIT_SUCCESS = 0


class AnalyzeCommand:
    def __init__(self, container: Container) -> None:
        self._container = container

    def execute(self) -> int:
        package = self._container.package_selector().select()
        options = self._container.options_prompt().ask()
        self._container.analyze_workflow().run_for(package, options)
        return _EXIT_SUCCESS
