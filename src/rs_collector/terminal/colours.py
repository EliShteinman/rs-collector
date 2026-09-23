import re

from pydantic import BaseModel, ConfigDict, Field

_SEQUENCE = re.compile(r"\x1b\[([0-9;]*)m")
_RESET = "0"
_BOLD = "1"
_FOREGROUND = {
    "30": "black",
    "31": "red",
    "32": "green",
    "33": "yellow",
    "34": "blue",
    "35": "magenta",
    "36": "cyan",
    "37": "white",
    "90": "grey",
    "91": "red",
    "92": "green",
    "93": "yellow",
    "94": "blue",
    "95": "magenta",
    "96": "cyan",
    "97": "white",
}


class Span(BaseModel):
    model_config = ConfigDict(frozen=True)

    text: str
    colour: str = Field(default="")
    bold: bool = Field(default=False)


def spans(line: str) -> tuple[Span, ...]:
    found: list[Span] = []
    colour = ""
    bold = False
    position = 0
    for match in _SEQUENCE.finditer(line):
        text = line[position : match.start()]
        if text:
            found.append(Span(text=text, colour=colour, bold=bold))
        colour, bold = _applied(match.group(1), colour, bold)
        position = match.end()
    remainder = line[position:]
    if remainder or not found:
        found.append(Span(text=remainder, colour=colour, bold=bold))
    return tuple(found)


def _applied(parameters: str, colour: str, bold: bool) -> tuple[str, bool]:
    for code in parameters.split(";"):
        if code in ("", _RESET):
            colour, bold = "", False
        elif code == _BOLD:
            bold = True
        elif code in _FOREGROUND:
            colour = _FOREGROUND[code]
    return colour, bold
