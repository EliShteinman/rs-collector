_MARKER_PREFIX = "RSC"
_CARRIAGE_RETURN = "\r"


class CommandOutputCleaner:
    """Keeps only what the command itself printed between its echo and its marker."""

    def clean(self, raw_output: str, command: str, marker: str) -> str:
        lines = [line.rstrip(_CARRIAGE_RETURN) for line in raw_output.splitlines()]
        body = lines[self._start_of_body(lines, command, marker) :]
        return "\n".join(line for line in body if marker not in line).strip()

    def _start_of_body(self, lines: list[str], command: str, marker: str) -> int:
        for position in reversed(range(len(lines))):
            if self._is_command_echo(lines[position], command, marker):
                return position + 1
        return 0

    def _is_command_echo(self, line: str, command: str, marker: str) -> bool:
        return command in line and marker in line


class MarkerFactory:
    def __init__(self, tokens: list[str] | None = None) -> None:
        self._tokens = list(tokens or [])
        self._counter = 0

    def next(self) -> str:
        if self._tokens:
            return self._tokens.pop(0)
        self._counter += 1
        return f"{_MARKER_PREFIX}_{self._counter}_{id(self):x}"
