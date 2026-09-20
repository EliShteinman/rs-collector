from typing import Protocol

from paramiko.channel import Channel

_ENCODING = "utf-8"
_DECODE_ERRORS = "replace"
_READ_SIZE = 65536


class ShellChannel(Protocol):
    def send(self, data: str) -> None: ...

    def receive(self) -> str: ...

    def is_open(self) -> bool: ...

    def close(self) -> None: ...


class ParamikoShellChannel:
    def __init__(self, channel: Channel) -> None:
        self._channel = channel

    def send(self, data: str) -> None:
        self._channel.sendall(data.encode(_ENCODING))

    def receive(self) -> str:
        if not self._channel.recv_ready():
            return ""
        return self._channel.recv(_READ_SIZE).decode(_ENCODING, errors=_DECODE_ERRORS)

    def is_open(self) -> bool:
        return not self._channel.closed and not self._channel.exit_status_ready()

    def close(self) -> None:
        self._channel.close()
