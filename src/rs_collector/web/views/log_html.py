from markupsafe import Markup, escape

from rs_collector.terminal.colours import Span, spans

_COLOUR_CLASS = "c-{colour}"
_BOLD_CLASS = "strong"


def as_html(line: str) -> Markup:
    return Markup("").join(_span(span) for span in spans(line))


def _span(span: Span) -> Markup:
    classes = [_COLOUR_CLASS.format(colour=span.colour)] if span.colour else []
    if span.bold:
        classes.append(_BOLD_CLASS)
    if not classes:
        return escape(span.text)
    return Markup('<span class="{}">{}</span>').format(" ".join(classes), span.text)
