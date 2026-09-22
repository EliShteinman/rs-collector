import pytest

from rs_collector.remote.output import CommandOutputCleaner, MarkerFactory

pytestmark = pytest.mark.unit


@pytest.fixture
def cleaner() -> CommandOutputCleaner:
    return CommandOutputCleaner()


def test_clean_drops_the_echoed_command(cleaner: CommandOutputCleaner) -> None:
    raw = "hostname; echo M:$?\r\nnode1\r\nM:0\r\n"

    assert cleaner.clean(raw, "hostname", "M") == "node1"


def test_clean_drops_output_left_over_from_earlier_commands(
    cleaner: CommandOutputCleaner,
) -> None:
    raw = "banner text\nhostname; echo M:$?\nnode1\nM:0\n"

    assert cleaner.clean(raw, "hostname", "M") == "node1"


def test_clean_keeps_every_output_line(cleaner: CommandOutputCleaner) -> None:
    raw = "cat file; echo M:$?\nfirst\nsecond\nM:0\n"

    assert cleaner.clean(raw, "cat file", "M") == "first\nsecond"


def test_clean_works_without_a_terminal_echo(cleaner: CommandOutputCleaner) -> None:
    assert cleaner.clean("node1\nM:0\n", "hostname", "M") == "node1"


def test_marker_factory_returns_unique_markers() -> None:
    factory = MarkerFactory()

    assert factory.next() != factory.next()


def test_marker_factory_returns_the_given_tokens_first() -> None:
    assert MarkerFactory(["M1"]).next() == "M1"
