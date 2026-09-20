from rs_collector.console.io import ConsoleIo

_AFFIRMATIVE = ("y", "yes")
_NEGATIVE = ("n", "no")


class ConfirmPrompt:
    def __init__(self, console: ConsoleIo) -> None:
        self._console = console

    def ask(self, question: str, default: bool) -> bool:
        while True:
            answer = self._console.read(f"{question} {self._hint(default)} ").strip().lower()
            if not answer:
                return default
            if answer in _AFFIRMATIVE:
                return True
            if answer in _NEGATIVE:
                return False
            self._console.write("Please answer with 'y' or 'n'.")

    def _hint(self, default: bool) -> str:
        return "[Y/n]" if default else "[y/N]"
