import socket
import subprocess
import threading
from collections.abc import Iterator
from pathlib import Path

import paramiko
import pytest

from rs_collector.exceptions.remote import HostKeyMismatchError
from rs_collector.inventory.models import Hostname
from rs_collector.remote.connector import ParamikoHostConnector
from rs_collector.settings.credentials import SshCredentials
from rs_collector.settings.models import AppSettings

pytestmark = pytest.mark.integration

_USER = "admin"
_PASSWORD = "secret"
_HOST = "localhost"


class _PasswordServer(paramiko.ServerInterface):
    def check_auth_password(self, username: str, password: str) -> int:
        if (username, password) == (_USER, _PASSWORD):
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def get_allowed_auths(self, username: str) -> str:
        return "password"


class LocalSshServer:
    def __init__(self, key_dir: Path) -> None:
        self._key_dir = key_dir
        self._generation = 0
        self.host_key = paramiko.Ed25519Key.from_private_key_file(self._new_key_file())
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind(("127.0.0.1", 0))
        self._socket.listen()
        self.port = self._socket.getsockname()[1]
        self._running = True
        self._transports: list[paramiko.Transport] = []
        threading.Thread(target=self._serve, daemon=True).start()

    def replace_host_key(self) -> None:
        self.host_key = paramiko.Ed25519Key.from_private_key_file(self._new_key_file())

    def close(self) -> None:
        self._running = False
        self._socket.close()
        for transport in self._transports:
            transport.close()

    def _serve(self) -> None:
        while self._running:
            try:
                connection, _ = self._socket.accept()
            except OSError:
                return
            transport = paramiko.Transport(connection)
            transport.add_server_key(self.host_key)
            self._transports.append(transport)
            try:
                transport.start_server(server=_PasswordServer())
            except paramiko.SSHException, EOFError, OSError:
                transport.close()

    def _new_key_file(self) -> str:
        self._generation += 1
        path = self._key_dir / f"host_key_{self._generation}"
        subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(path)], check=True)
        return str(path)


@pytest.fixture
def server(tmp_path_factory: pytest.TempPathFactory) -> Iterator[LocalSshServer]:
    running = LocalSshServer(tmp_path_factory.mktemp("server"))
    yield running
    running.close()


@pytest.fixture
def connector(
    server: LocalSshServer, app_settings: AppSettings, tmp_path: Path
) -> ParamikoHostConnector:
    credentials = SshCredentials(ssh_user=_USER, ssh_password=_PASSWORD)

    class _PortClient(paramiko.SSHClient):
        def connect(self, hostname: str, **arguments: object) -> None:
            super().connect(hostname, port=server.port, **arguments)

    return ParamikoHostConnector(
        credentials, app_settings.remote, tmp_path / "known_hosts", client_factory=_PortClient
    )


def test_the_first_connection_records_the_host_key(
    connector: ParamikoHostConnector, tmp_path: Path, server: LocalSshServer
) -> None:
    connector.connect(Hostname(value=_HOST)).close()

    assert server.host_key.get_base64() in (tmp_path / "known_hosts").read_text()


def test_a_known_host_connects_again(connector: ParamikoHostConnector) -> None:
    connector.connect(Hostname(value=_HOST)).close()

    connector.connect(Hostname(value=_HOST)).close()


def test_a_changed_host_key_is_refused(
    connector: ParamikoHostConnector, server: LocalSshServer
) -> None:
    connector.connect(Hostname(value=_HOST)).close()
    server.replace_host_key()

    with pytest.raises(HostKeyMismatchError):
        connector.connect(Hostname(value=_HOST))
