from rs_collector.analysis.options import AnalysisDepth, AnalysisOptions
from rs_collector.console.choice import ChoicePrompt
from rs_collector.console.io import ConsoleIo

_BDB_QUESTION = "Database to analyze (Enter for every database): "
_BDB_ERROR = "Please answer with a database number or press Enter."
_DEPTH_TITLE = "Analysis depth (Enter for the default):"
_MASK_TITLE = "Mask sensitive values (Enter for no):"
_DEPTH_LABELS: dict[AnalysisDepth, str] = {
    AnalysisDepth.QUICK: "quick - skip the logs",
    AnalysisDepth.DEFAULT: "default",
    AnalysisDepth.FULL: "full - force a full analysis",
    AnalysisDepth.MAX: "max - full analysis and pattern counts",
}
_MASK_LABELS = ("no", "yes")
_DEFAULT_DEPTH_INDEX = 1
_DEFAULT_MASK_INDEX = 0


class AnalysisOptionsPrompt:
    def __init__(self, console: ConsoleIo, choices: ChoicePrompt | None = None) -> None:
        self._console = console
        self._choices = choices or ChoicePrompt(console)

    def ask(self) -> AnalysisOptions:
        return AnalysisOptions(
            bdb_id=self._ask_bdb(), depth=self._ask_depth(), mask=self._ask_mask()
        )

    def _ask_bdb(self) -> int | None:
        while True:
            answer = self._console.read(_BDB_QUESTION).strip()
            if not answer:
                return None
            if answer.isdigit() and int(answer) > 0:
                return int(answer)
            self._console.write(_BDB_ERROR)

    def _ask_depth(self) -> AnalysisDepth:
        depths = tuple(_DEPTH_LABELS)
        index = self._choices.select_with_default(
            _DEPTH_TITLE, tuple(_DEPTH_LABELS.values()), _DEFAULT_DEPTH_INDEX
        )
        return depths[index]

    def _ask_mask(self) -> bool:
        index = self._choices.select_with_default(_MASK_TITLE, _MASK_LABELS, _DEFAULT_MASK_INDEX)
        return bool(index)
