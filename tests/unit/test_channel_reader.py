import re

import pytest
from tests.fakes import FakeShellChannel

from rs_collector.exceptions.remote import RemoteCommandError, RemoteCommandTimeoutError
from rs_collector.remote.channel_reader import ChannelReader
from rs_collector.runtime.clock import FrozenClock

pytestmark = pytest.mark.unit


def _reader(channel: FakeShellChannel) -> ChannelReader:
    return ChannelReader(channel, clock=FrozenClock(), poll_interval_seconds=1.0)


def test_read_until_any_returns_the_buffer_holding_the_marker() -> None:
    channel = FakeShellChannel(["hello ", "world MARK"])

    assert _reader(channel).read_until_any(["MARK"], timeout_seconds=10) == "hello world MARK"


def test_read_until_pattern_exposes_the_match() -> None:
    channel = FakeShellChannel(["done RSC_1:0\n"])

    _, match = _reader(channel).read_until_pattern(re.compile(r"RSC_1:(\d+)"), timeout_seconds=10)

    assert match.group(1) == "0"


def test_read_stops_when_the_timeout_passes() -> None:
    channel = FakeShellChannel([])

    with pytest.raises(RemoteCommandTimeoutError):
        _reader(channel).read_until_any(["MARK"], timeout_seconds=2)


def test_read_stops_when_the_channel_closes() -> None:
    channel = FakeShellChannel([])
    channel.close()

    with pytest.raises(RemoteCommandError):
        _reader(channel).read_until_any(["MARK"], timeout_seconds=10)
