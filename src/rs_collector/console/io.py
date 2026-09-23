import sys
from typing import Protocol, TextIO

from rs_collector.exceptions.selection import SelectionAbortedError


class ConsoleIo(Protocol):
    def write(self, message: str) -> None: ...

    def write_over(self, message: str) -> None: ...

    def read(self, prompt: str) -> str: ...


class StandardConsole:
    def __init__(self, stream: TextIO | None = None) -> None:
        self._stream = stream or sys.stdout
        self._open_line = False

    def _finish_the_open_line(self) -> None:
        if self._open_line:
            print(file=self._stream)
            self._open_line = False

    def write(self, message: str) -> None:
        self._finish_the_open_line()
        print(message, file=self._stream)

    def write_over(self, message: str) -> None:
        print(f"\r{message}", end="", file=self._stream, flush=True)
        self._open_line = True

    def read(self, prompt: str) -> str:
        try:
            return input(prompt)
        except (EOFError, KeyboardInterrupt) as error:
            raise SelectionAbortedError("Input was interrupted") from error


class ScriptedConsole:
    def __init__(self, answers: list[str]) -> None:
        self._answers = list(answers)
        self.written: list[str] = []

    def write(self, message: str) -> None:
        self.written.append(message)

    def write_over(self, message: str) -> None:
        if self.written:
            self.written[-1] = message
            return
        self.written.append(message)

    def read(self, prompt: str) -> str:
        self.written.append(prompt)
        if not self._answers:
            raise SelectionAbortedError("No answer left for the prompt")
        return self._answers.pop(0)
