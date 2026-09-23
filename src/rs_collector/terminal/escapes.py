import re

_ESCAPE = re.compile(r"\x1b(?:\][^\x07\x1b]*(?:\x07|\x1b\\)|\[[0-?]*[ -/]*[@-~]|[@-Z\\^_])")
_CARRIAGE_RETURN = "\r"
_BACKSPACE = "\x08"


def plain(text: str) -> str:
    return _ESCAPE.sub("", text).replace(_BACKSPACE, "")


def as_shown(line: str) -> str:
    return plain(line.rsplit(_CARRIAGE_RETURN, maxsplit=1)[-1])
