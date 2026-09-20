from typing import Any, Protocol

from paramiko import AutoAddPolicy, RejectPolicy, SSHClient
from paramiko.ssh_exception import SSHException

from rs_collector.exceptions.remote import SshConnectionError
from rs_collector.inventory.models import Hostname
from rs_collector.logging_setup.configurator import LoggerFactory
from rs_collector.remote.session import ParamikoSshSession, SshSession
from rs_collector.settings.credentials import SshCredentials
from rs_collector.settings.models import RemoteSettings


class HostConnector(Protocol):
    def connect(self, host: Hostname) -> SshSession: ...


class ParamikoHostConnector:
    def __init__(self, credentials: SshCredentials, settings: RemoteSettings) -> None:
        self._credentials = credentials
        self._settings = settings
        self._logger = LoggerFactory.for_component("remote.connector")

    def connect(self, host: Hostname) -> SshSession:
        client = SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(self._host_key_policy())
        self._logger.debug("Connecting to %s as %s", host, self._credentials.require_user())
        try:
            client.connect(hostname=host.value, **self._connect_arguments())
        except (SSHException, OSError) as error:
            client.close()
            raise SshConnectionError(f"{host} is not reachable over SSH: {error}") from error
        self._logger.info("Connected to %s", host)
        return ParamikoSshSession(client, host.value)

    def _host_key_policy(self) -> AutoAddPolicy | RejectPolicy:
        return AutoAddPolicy() if self._settings.auto_accept_host_keys else RejectPolicy()

    def _connect_arguments(self) -> dict[str, Any]:
        credentials = self._credentials.validated()
        arguments: dict[str, Any] = {
            "username": credentials.require_user(),
            "timeout": self._settings.connect_timeout_seconds,
            "auth_timeout": self._settings.connect_timeout_seconds,
            "allow_agent": False,
            "look_for_keys": False,
        }
        if credentials.has_key():
            arguments["key_filename"] = str(credentials.ssh_key_path)
        if credentials.has_password():
            arguments["password"] = credentials.ssh_password.get_secret_value()
        return arguments
