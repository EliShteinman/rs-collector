from collections.abc import Sequence

from rs_collector.console.io import ConsoleIo

_FIRST_INDEX = 1


class ChoicePrompt:
    def __init__(self, console: ConsoleIo) -> None:
        self._console = console

    def select(self, title: str, options: Sequence[str]) -> int:
        self._console.write(title)
        for position, option in enumerate(options, start=_FIRST_INDEX):
            self._console.write(f"  {position}) {option}")
        return self._ask_until_valid(len(options))

    def _ask_until_valid(self, count: int) -> int:
        while True:
            answer = self._console.read(f"Choice [{_FIRST_INDEX}-{count}]: ").strip()
            index = self._as_index(answer, count)
            if index is not None:
                return index
            self._console.write(f"Please answer with a number between {_FIRST_INDEX} and {count}.")

    def _as_index(self, answer: str, count: int) -> int | None:
        if not answer.isdigit():
            return None
        position = int(answer)
        if not _FIRST_INDEX <= position <= count:
            return None
        return position - _FIRST_INDEX
