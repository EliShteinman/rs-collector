from dataclasses import dataclass

from rs_collector.exceptions.remote import ClusterUnreachableError, SshConnectionError
from rs_collector.inventory.models import Cluster, Hostname
from rs_collector.logging_setup.configurator import LoggerFactory
from rs_collector.remote.connector import HostConnector
from rs_collector.remote.session import SshSession


@dataclass(frozen=True, slots=True)
class ClusterConnection:
    cluster: Cluster
    host: Hostname
    session: SshSession

    def close(self) -> None:
        self.session.close()


class ClusterConnector:
    def __init__(self, connector: HostConnector) -> None:
        self._connector = connector
        self._logger = LoggerFactory.for_component("remote.cluster")

    def connect(self, cluster: Cluster) -> ClusterConnection:
        failures: list[str] = []
        for host in cluster.hosts_in_connection_order():
            connection = self._try_host(cluster, host, failures)
            if connection is not None:
                return connection
        self._logger.error("No host of %s accepted a connection", cluster.name)
        raise ClusterUnreachableError(
            f"No host of cluster {cluster.name} is reachable: {'; '.join(failures)}"
        )

    def _try_host(
        self, cluster: Cluster, host: Hostname, failures: list[str]
    ) -> ClusterConnection | None:
        try:
            session = self._connector.connect(host)
        except SshConnectionError as error:
            self._logger.warning("Host %s is unreachable, trying the next one: %s", host, error)
            failures.append(f"{host}: {error}")
            return None
        return ClusterConnection(cluster=cluster, host=host, session=session)
