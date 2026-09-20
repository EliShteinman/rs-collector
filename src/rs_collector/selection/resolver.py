from rs_collector.exceptions.selection import ClusterNotFoundError
from rs_collector.inventory.models import Cluster, Hostname, Inventory
from rs_collector.logging_setup.configurator import LoggerFactory

_DOMAIN_SEPARATOR = "."


class ClusterResolver:
    def __init__(self) -> None:
        self._logger = LoggerFactory.for_component("selection")

    def resolve(self, host: Hostname, inventory: Inventory) -> Cluster:
        matches = [cluster for cluster in inventory.clusters if self._matches(host, cluster)]
        if not matches:
            raise ClusterNotFoundError(f"No cluster in the inventory matches '{host}'")
        cluster = max(matches, key=lambda candidate: len(candidate.name))
        self._logger.info("Host %s resolved to cluster %s", host, cluster.name)
        return cluster

    def _matches(self, host: Hostname, cluster: Cluster) -> bool:
        return any(self._same_or_subdomain(host, known) for known in self._known_hosts(cluster))

    def _known_hosts(self, cluster: Cluster) -> tuple[Hostname, ...]:
        return cluster.hosts_in_connection_order()

    def _same_or_subdomain(self, host: Hostname, known: Hostname) -> bool:
        return host.value == known.value or host.value.endswith(f"{_DOMAIN_SEPARATOR}{known.value}")
