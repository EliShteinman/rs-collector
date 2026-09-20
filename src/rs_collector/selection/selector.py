from typing import Protocol

from rs_collector.inventory.models import Cluster


class ClusterSelector(Protocol):
    def select(self) -> Cluster: ...
