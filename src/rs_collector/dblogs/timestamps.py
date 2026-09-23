import re
from datetime import datetime

_REDIS_PREFIX = re.compile(r"^\d+:[A-Za-z]+\s+")
_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"^(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2})"), "%Y-%m-%d %H:%M:%S"),
    (re.compile(r"^(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2})"), "%Y/%m/%d %H:%M:%S"),
    (re.compile(r"^(\d{1,2} [A-Za-z]{3} \d{4} \d{2}:\d{2}:\d{2})"), "%d %b %Y %H:%M:%S"),
    (re.compile(r"^([A-Za-z]{3} \d{1,2} \d{4} \d{2}:\d{2}:\d{2})"), "%b %d %Y %H:%M:%S"),
    (re.compile(r"^(\d{1,2} [A-Za-z]{3} \d{2}:\d{2}:\d{2})"), "%d %b %H:%M:%S"),
    (re.compile(r"^([A-Za-z]{3} \d{1,2} \d{2}:\d{2}:\d{2})"), "%b %d %H:%M:%S"),
)


def first_moment(line: str) -> datetime | None:
    text = _REDIS_PREFIX.sub("", line.replace("T", " ", 1) if _looks_iso(line) else line).lstrip()
    for pattern, layout in _PATTERNS:
        match = pattern.match(text)
        if match is None:
            continue
        try:
            return datetime.strptime(match.group(1), layout)
        except ValueError:
            continue
    return None


def _looks_iso(line: str) -> bool:
    return bool(re.match(r"^\d{4}-\d{2}-\d{2}T", line))
