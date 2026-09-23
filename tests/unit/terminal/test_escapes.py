import pytest

from rs_collector.terminal.escapes import as_shown, plain

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("\x1b[32mdone\x1b[0m", "done"),
        ("\x1b[1;31mERROR\x1b[m broken", "ERROR broken"),
        ("plain text", "plain text"),
        ("clearing\x1b[2K", "clearing"),
        ("\x1b]0;title\x07after", "after"),
        ("typo\x08\x08fixed", "typofixed"),
    ],
)
def test_the_colours_and_controls_are_removed(raw: str, expected: str) -> None:
    assert plain(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("10%\r55%\r100%", "100%"),
        ("\x1b[32m10%\x1b[0m\rdone", "done"),
        ("no carriage return", "no carriage return"),
    ],
)
def test_only_what_the_terminal_would_show_is_kept(raw: str, expected: str) -> None:
    assert as_shown(raw) == expected
