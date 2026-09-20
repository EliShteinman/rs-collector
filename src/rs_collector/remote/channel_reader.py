import re
from collections.abc import Sequence

from rs_collector.exceptions.remote import RemoteCommandError, RemoteCommandTimeoutError
from rs_collector.remote.channel import ShellChannel
from rs_collector.runtime.clock import Clock, SystemClock

_POLL_INTERVAL_SECONDS = 0.1


class ChannelReader:
    def __init__(
        self,
        channel: ShellChannel,
        clock: Clock | None = None,
        poll_interval_seconds: float = _POLL_INTERVAL_SECONDS,
    ) -> None:
        self._channel = channel
        self._clock = clock or SystemClock()
        self._poll_interval_seconds = poll_interval_seconds

    def read_until_any(self, markers: Sequence[str], timeout_seconds: float) -> str:
        pattern = re.compile("|".join(re.escape(marker) for marker in markers))
        return self.read_until_pattern(pattern, timeout_seconds)[0]

    def read_until_pattern(
        self, pattern: re.Pattern[str], timeout_seconds: float
    ) -> tuple[str, re.Match[str]]:
        deadline = self._clock.now() + timeout_seconds
        buffer = ""
        while True:
            buffer += self._channel.receive()
            match = pattern.search(buffer)
            if match is not None:
                return buffer, match
            self._guard(buffer, deadline)
            self._clock.sleep(self._poll_interval_seconds)

    def _guard(self, buffer: str, deadline: float) -> None:
        if not self._channel.is_open():
            raise RemoteCommandError(f"The remote shell closed unexpectedly. Output: {buffer!r}")
        if self._clock.now() >= deadline:
            raise RemoteCommandTimeoutError(
                f"The remote shell produced no expected output in time. Output: {buffer!r}"
            )
