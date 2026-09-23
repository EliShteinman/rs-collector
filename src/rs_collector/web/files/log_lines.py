import re

from pydantic import BaseModel, ConfigDict, Field

from rs_collector.terminal.escapes import as_shown

_ENCODING = "utf-8"
_LEVEL_WORDS = (
    ("critical", re.compile(r"\b(critical|fatal|panic)\b", re.IGNORECASE)),
    ("error", re.compile(r"\b(error|err|failed|failure|exception|traceback)\b", re.IGNORECASE)),
    ("warning", re.compile(r"\b(warning|warn)\b", re.IGNORECASE)),
    ("notice", re.compile(r"\b(notice)\b", re.IGNORECASE)),
    ("info", re.compile(r"\b(info)\b", re.IGNORECASE)),
    ("debug", re.compile(r"\b(debug|trace)\b", re.IGNORECASE)),
)
_REDIS_MARKER = re.compile(r"^\d+:[A-Za-z]+ .{0,40}?([#*\-.]) ")
_REDIS_LEVELS = {"#": "warning", "*": "notice", "-": "info", ".": "debug"}
_PREFIX_LENGTH = 160
_PLAIN = "plain"
_BREAK = "\n"
_WINDOWS_BREAK = "\r\n"


class LogLine(BaseModel):
    model_config = ConfigDict(frozen=True)

    number: int = Field(gt=0)
    level: str
    text: str


class LogContent(BaseModel):
    model_config = ConfigDict(frozen=True)

    lines: tuple[LogLine, ...]
    total_lines: int = Field(ge=0)

    @property
    def is_complete(self) -> bool:
        return len(self.lines) == self.total_lines

    def levels(self) -> tuple[str, ...]:
        seen = {line.level for line in self.lines}
        ordered = (*(name for name, _ in _LEVEL_WORDS), _PLAIN)
        return tuple(level for level in ordered if level in seen)


class LogReader:
    def __init__(self, max_lines: int) -> None:
        self._max_lines = max_lines

    def parse(self, content: bytes) -> LogContent:
        text = content.decode(_ENCODING, errors="replace")
        rows = [as_shown(row) for row in _rows(text)]
        shown = rows[-self._max_lines :] if len(rows) > self._max_lines else rows
        first = len(rows) - len(shown) + 1
        return LogContent(
            lines=tuple(
                LogLine(number=first + offset, level=level_of(row), text=row)
                for offset, row in enumerate(shown)
            ),
            total_lines=len(rows),
        )


def level_of(line: str) -> str:
    candidates = [_marker_level(line), _word_level(line)]
    found = [level for level in candidates if level is not None]
    return min(found, key=_severity) if found else _PLAIN


def _severity(level: str) -> int:
    order = [name for name, _ in _LEVEL_WORDS]
    return order.index(level) if level in order else len(order)


def _marker_level(line: str) -> str | None:
    marker = _REDIS_MARKER.match(line)
    return _REDIS_LEVELS[marker.group(1)] if marker is not None else None


def _word_level(line: str) -> str | None:
    head = line[:_PREFIX_LENGTH]
    for name, pattern in _LEVEL_WORDS:
        if pattern.search(head):
            return name
    return None


def _rows(text: str) -> list[str]:
    rows = text.replace(_WINDOWS_BREAK, _BREAK).split(_BREAK)
    if rows and not rows[-1]:
        rows.pop()
    return rows
