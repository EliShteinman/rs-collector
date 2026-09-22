from collections.abc import Iterable, Sequence
from pathlib import Path

from rs_collector.exceptions.remote import SshConnectionError
from rs_collector.inventory.models import Hostname
from rs_collector.remote.channel import ShellChannel
from rs_collector.remote.models import CommandResult


class FakeShellChannel:
    def __init__(self, responses: Iterable[str] = ()) -> None:
        self._responses = list(responses)
        self.sent: list[str] = []
        self._open = True

    def queue(self, response: str) -> None:
        self._responses.append(response)

    def send(self, data: str) -> None:
        self.sent.append(data)

    def receive(self) -> str:
        return self._responses.pop(0) if self._responses else ""

    def is_open(self) -> bool:
        return self._open

    def close(self) -> None:
        self._open = False


class ScriptedShellChannel:
    def __init__(self, replies: dict[str, str], default_reply: str = "") -> None:
        self._replies = replies
        self._default_reply = default_reply
        self._pending: list[str] = []
        self.sent: list[str] = []
        self._open = True

    def send(self, data: str) -> None:
        line = data.strip()
        self.sent.append(line)
        self._pending.append(self._reply_for(line))

    def _reply_for(self, line: str) -> str:
        for trigger, reply in self._replies.items():
            if trigger in line:
                return self._echo(line) + reply.replace("{marker}", self._marker_of(line))
        if "echo " not in line:
            return ""
        return self._echo(line) + self._default_reply.replace("{marker}", self._marker_of(line))

    def _echo(self, line: str) -> str:
        return f"{line}\n" if "echo " in line else ""

    def _marker_of(self, line: str) -> str:
        if "echo " not in line:
            return ""
        return line.rsplit("echo ", maxsplit=1)[1].split(":", maxsplit=1)[0]

    def receive(self) -> str:
        return self._pending.pop(0) if self._pending else ""

    def is_open(self) -> bool:
        return self._open

    def close(self) -> None:
        self._open = False


class FakeSshSession:
    def __init__(self, channel: ShellChannel | None = None) -> None:
        self.channel = channel or FakeShellChannel()
        self.commands: list[str] = []
        self.downloads: list[tuple[str, Path]] = []
        self.closed = False
        self.results: dict[str, CommandResult] = {}
        self.download_payload = b"package"

    def run(self, command: str, timeout_seconds: int) -> CommandResult:
        self.commands.append(command)
        if command in self.results:
            return self.results[command]
        return CommandResult(command=command, exit_status=0, output="")

    def open_shell(self) -> ShellChannel:
        return self.channel

    def download(self, remote_path: str, local_path: Path) -> None:
        self.downloads.append((remote_path, local_path))
        local_path.write_bytes(self.download_payload)

    def close(self) -> None:
        self.closed = True


class FakeHostConnector:
    def __init__(self, reachable: dict[str, FakeSshSession]) -> None:
        self._reachable = reachable
        self.attempts: list[str] = []

    def connect(self, host: Hostname) -> FakeSshSession:
        self.attempts.append(host.value)
        session = self._reachable.get(host.value)
        if session is None:
            raise SshConnectionError(f"{host} refused the connection")
        return session


class FakeProcessRunner:
    def __init__(self, exit_status: int = 0, error: Exception | None = None) -> None:
        self.exit_status = exit_status
        self.error = error
        self.calls: list[tuple[tuple[str, ...], Path, Path, int]] = []

    def run(self, command: Iterable[str], cwd: Path, log_path: Path, timeout_seconds: int) -> int:
        self.calls.append((tuple(command), cwd, log_path, timeout_seconds))
        if self.error is not None:
            raise self.error
        log_path.write_text("analyzer output\n", encoding="utf-8")
        return self.exit_status


class FakeCrontab:
    def __init__(self, content: str = "") -> None:
        self.content = content

    def read(self) -> str:
        return self.content

    def write(self, content: str) -> None:
        self.content = content


class FakeProgram:
    def __init__(self, *prefix: str) -> None:
        self._prefix = prefix or ("/usr/local/bin/rsc",)

    def argv(self, *arguments: str) -> tuple[str, ...]:
        return (*self._prefix, *arguments)


class FakeSpawner:
    def __init__(self, pid: int = 4242) -> None:
        self._pid = pid
        self.spawned: list[tuple[str, ...]] = []

    def spawn(self, argv: Sequence[str], log_path: Path) -> int:
        self.spawned.append(tuple(argv))
        return self._pid


class FakeProcessSignals:
    def __init__(self, alive: set[int] | None = None, dies_on_terminate: bool = True) -> None:
        self.alive = set() if alive is None else alive
        self._dies_on_terminate = dies_on_terminate
        self.terminated: list[int] = []

    def is_alive(self, pid: int) -> bool:
        return pid in self.alive

    def terminate(self, pid: int) -> None:
        self.terminated.append(pid)
        if self._dies_on_terminate:
            self.alive.discard(pid)
