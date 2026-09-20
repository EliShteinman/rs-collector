from rs_collector.inventory.models import Cluster
from rs_collector.inventory.repository import InventoryRepository
from rs_collector.selection.connection_string import ConnectionStringParser
from rs_collector.selection.resolver import ClusterResolver


class ConnectionStringClusterSelector:
    def __init__(
        self,
        connection_string: str,
        repository: InventoryRepository,
        parser: ConnectionStringParser,
        resolver: ClusterResolver,
    ) -> None:
        self._connection_string = connection_string
        self._repository = repository
        self._parser = parser
        self._resolver = resolver

    def select(self) -> Cluster:
        target = self._parser.parse(self._connection_string)
        return self._resolver.resolve(target.host, self._repository.load())
