from pathlib import Path
from typing import Protocol, Self

from paramiko import SSHClient
from paramiko.ssh_exception import SSHException

from rs_collector.exceptions.remote import FileTransferError, RemoteCommandError
from rs_collector.logging_setup.configurator import LoggerFactory
from rs_collector.remote.channel import ParamikoShellChannel, ShellChannel
from rs_collector.remote.models import CommandResult

_ENCODING = "utf-8"
_DECODE_ERRORS = "replace"
_TERMINAL_WIDTH = 512


class SshSession(Protocol):
    def run(self, command: str, timeout_seconds: int) -> CommandResult: ...

    def open_shell(self) -> ShellChannel: ...

    def download(self, remote_path: str, local_path: Path) -> None: ...

    def close(self) -> None: ...


class ParamikoSshSession:
    def __init__(self, client: SSHClient, host: str) -> None:
        self._client = client
        self._host = host
        self._logger = LoggerFactory.for_component("remote.session")

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def run(self, command: str, timeout_seconds: int) -> CommandResult:
        self._logger.debug("Running on %s: %s", self._host, command)
        try:
            _, stdout, stderr = self._client.exec_command(command, timeout=timeout_seconds)
            output = stdout.read().decode(_ENCODING, errors=_DECODE_ERRORS)
            errors = stderr.read().decode(_ENCODING, errors=_DECODE_ERRORS)
            exit_status = stdout.channel.recv_exit_status()
        except (SSHException, OSError) as error:
            raise RemoteCommandError(f"'{command}' failed on {self._host}: {error}") from error
        return CommandResult(
            command=command, exit_status=exit_status, output=f"{output}{errors}".strip()
        )

    def open_shell(self) -> ShellChannel:
        try:
            channel = self._client.invoke_shell(width=_TERMINAL_WIDTH)
        except SSHException as error:
            raise RemoteCommandError(
                f"No interactive shell could be opened on {self._host}: {error}"
            ) from error
        return ParamikoShellChannel(channel)

    def download(self, remote_path: str, local_path: Path) -> None:
        self._logger.info("Downloading %s:%s to %s", self._host, remote_path, local_path)
        try:
            with self._client.open_sftp() as sftp:
                sftp.get(remote_path, str(local_path))
        except (SSHException, OSError) as error:
            raise FileTransferError(
                f"{remote_path} could not be downloaded from {self._host}: {error}"
            ) from error

    def close(self) -> None:
        self._logger.debug("Closing the connection to %s", self._host)
        self._client.close()
