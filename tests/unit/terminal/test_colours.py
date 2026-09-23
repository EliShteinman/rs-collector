import pytest

from rs_collector.terminal.colours import spans

pytestmark = pytest.mark.unit


def test_plain_text_is_one_span_without_colour() -> None:
    assert spans("nothing special") == (
        type(spans("x")[0])(text="nothing special", colour="", bold=False),
    )


def test_a_coloured_word_keeps_its_colour() -> None:
    found = spans("status: \x1b[32mok\x1b[0m")

    assert [(span.text, span.colour) for span in found] == [("status: ", ""), ("ok", "green")]


def test_a_bold_colour_is_kept() -> None:
    found = spans("\x1b[1;31mbroken\x1b[0m")

    assert (found[0].text, found[0].colour, found[0].bold) == ("broken", "red", True)


def test_a_reset_ends_the_colour() -> None:
    found = spans("\x1b[33mwarn\x1b[0m then plain")

    assert [(span.text, span.colour) for span in found] == [("warn", "yellow"), (" then plain", "")]


def test_the_bright_colours_are_recognized() -> None:
    assert spans("\x1b[92mready")[0].colour == "green"


def test_an_unknown_code_leaves_the_text_alone() -> None:
    found = spans("\x1b[7minverted\x1b[0m")

    assert found[0].text == "inverted"
