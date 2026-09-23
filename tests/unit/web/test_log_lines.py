import pytest

from rs_collector.web.files.log_lines import LogReader, level_of
from rs_collector.web.views.log_html import as_html

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        ("2026-09-23 07:41:02 ERROR could not reach node2", "error"),
        ("2026-09-23 07:41:02 WARNING memory is above 80%", "warning"),
        ("2026-09-23 07:41:02 INFO cluster is healthy", "info"),
        ("2026-09-23 07:41:02 DEBUG polling", "debug"),
        ("2026-09-23 07:41:02 CRITICAL node lost", "critical"),
        ("a line with nothing special", "plain"),
    ],
)
def test_the_level_of_a_line_is_recognized(line: str, expected: str) -> None:
    assert level_of(line) == expected


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        ("12:M 23 Sep 2026 07:41:02.123 * Background saving started", "notice"),
        ("12:M 23 Sep 2026 07:41:02.123 # Server initialized", "warning"),
        ("12:M 23 Sep 2026 07:41:02.123 - DB saved on disk", "info"),
        ("12:M 23 Sep 2026 07:41:02.123 . tracing", "debug"),
    ],
)
def test_the_redis_log_markers_are_recognized(line: str, expected: str) -> None:
    assert level_of(line) == expected


def test_every_line_is_numbered() -> None:
    content = LogReader(max_lines=100).parse(b"first\nsecond\nthird\n")

    assert [line.number for line in content.lines] == [1, 2, 3]


def test_a_long_log_shows_its_last_lines() -> None:
    rows = "\n".join(f"line {number}" for number in range(1, 1001)).encode("utf-8")

    content = LogReader(max_lines=10).parse(rows)

    assert content.total_lines == 1000
    assert content.lines[0].number == 991
    assert not content.is_complete


def test_a_short_log_is_complete() -> None:
    assert LogReader(max_lines=10).parse(b"only one line\n").is_complete


def test_the_levels_present_are_listed() -> None:
    content = LogReader(max_lines=10).parse(b"ERROR broken\nplain line\nWARNING careful\n")

    assert content.levels() == ("error", "warning", "plain")


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        ("4711:M 23 Sep 2026 08:12:44.301 # ERROR Failed to fork", "error"),
        ("4711:M 23 Sep 2026 08:12:44.301 # WARNING Memory usage is high", "warning"),
        ("4711:M 23 Sep 2026 08:12:44.301 * Background saving started", "notice"),
    ],
)
def test_the_strongest_signal_in_a_redis_line_wins(line: str, expected: str) -> None:
    assert level_of(line) == expected


def test_a_progress_line_shows_only_what_the_terminal_would_show() -> None:
    content = LogReader(max_lines=10).parse(b"reading 10%\rreading 60%\rreading 100%\ndone\n")

    assert [line.text for line in content.lines] == ["reading 100%", "done"]


def test_the_colours_are_kept_and_the_level_still_read() -> None:
    content = LogReader(max_lines=10).parse(b"\x1b[31mERROR broken\x1b[0m\n")

    assert content.lines[0].text == "\x1b[31mERROR broken\x1b[0m"
    assert content.lines[0].level == "error"


def test_a_coloured_line_becomes_coloured_markup() -> None:
    markup = str(as_html("\x1b[31mERROR broken\x1b[0m"))

    assert markup == '<span class="c-red">ERROR broken</span>'


def test_markup_from_a_log_line_is_escaped() -> None:
    markup = str(as_html("<script>alert(1)</script>"))

    assert "&lt;script&gt;" in markup
