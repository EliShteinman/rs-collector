from types import TracebackType
from typing import Self

from pydantic import SecretStr

from rs_collector.logging_setup.configurator import LoggerFactory
from rs_collector.remote.channel_reader import ChannelReader
from rs_collector.remote.cluster_connector import ClusterConnection
from rs_collector.remote.root_shell import RootShell
from rs_collector.settings.models import RemoteSettings


class RootSession:
    def __init__(
        self,
        connection: ClusterConnection,
        settings: RemoteSettings,
        sudo_password: SecretStr | None = None,
    ) -> None:
        self._connection = connection
        self._settings = settings
        self._sudo_password = sudo_password
        self._shell: RootShell | None = None
        self._logger = LoggerFactory.for_component("remote.root_session")

    def __enter__(self) -> Self:
        channel = self._connection.session.open_shell()
        shell = RootShell(
            channel=channel,
            reader=ChannelReader(channel),
            settings=self._settings,
            sudo_password=self._sudo_password,
        )
        shell.escalate()
        self._shell = shell
        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self._logger.debug("Leaving the root session on %s", self._connection.host)
        self._connection.close()

    @property
    def shell(self) -> RootShell:
        if self._shell is None:
            raise RuntimeError("The root session is not open")
        return self._shell

    @property
    def connection(self) -> ClusterConnection:
        return self._connection
