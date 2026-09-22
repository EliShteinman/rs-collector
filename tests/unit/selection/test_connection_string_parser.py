import pytest

from rs_collector.exceptions.selection import ConnectionStringError
from rs_collector.selection.connection_string import ConnectionStringParser

pytestmark = pytest.mark.unit


@pytest.fixture
def parser() -> ConnectionStringParser:
    return ConnectionStringParser()


@pytest.mark.parametrize(
    ("connection_string", "expected_host"),
    [
        ("redis://user:secret@c1.example.com:12000", "c1.example.com"),
        ("rediss://c1.example.com:12000", "c1.example.com"),
        ("c1.example.com:12000", "c1.example.com"),
        ("c1.example.com", "c1.example.com"),
        ("  C1.Example.com  ", "c1.example.com"),
    ],
)
def test_parse_extracts_the_host(
    parser: ConnectionStringParser, connection_string: str, expected_host: str
) -> None:
    assert parser.parse(connection_string).host.value == expected_host


def test_parse_extracts_the_port(parser: ConnectionStringParser) -> None:
    assert parser.parse("redis://c1.example.com:12000").port == 12000


def test_parse_leaves_the_port_empty_when_absent(parser: ConnectionStringParser) -> None:
    assert parser.parse("c1.example.com").port is None


@pytest.mark.parametrize(
    "connection_string",
    ["", "   ", "http://c1.example.com", "redis://", "redis://bad_host:12000"],
)
def test_parse_rejects_invalid_input(
    parser: ConnectionStringParser, connection_string: str
) -> None:
    with pytest.raises(ConnectionStringError):
        parser.parse(connection_string)
