from rs_collector.console.choice import ChoicePrompt
from rs_collector.exceptions.selection import EmptyInventoryError
from rs_collector.inventory.models import Cluster, Environment, Inventory
from rs_collector.inventory.repository import InventoryRepository
from rs_collector.logging_setup.configurator import LoggerFactory

_ENVIRONMENT_TITLE = "Select an environment:"
_CLUSTER_TITLE = "Select a cluster:"


class InteractiveClusterSelector:
    def __init__(self, repository: InventoryRepository, prompt: ChoicePrompt) -> None:
        self._repository = repository
        self._prompt = prompt
        self._logger = LoggerFactory.for_component("selection")

    def select(self) -> Cluster:
        inventory = self._repository.load()
        environment = self._select_environment(inventory)
        cluster = self._select_cluster(environment)
        self._logger.info("Cluster %s selected interactively", cluster.name)
        return cluster

    def _select_environment(self, inventory: Inventory) -> Environment:
        if inventory.is_empty():
            raise EmptyInventoryError("The inventory holds no environment")
        names = inventory.environment_names()
        if len(names) == 1:
            return inventory.environments[0]
        index = self._prompt.select(_ENVIRONMENT_TITLE, names)
        return inventory.environments[index]

    def _select_cluster(self, environment: Environment) -> Cluster:
        names = tuple(cluster.name for cluster in environment.clusters)
        if len(names) == 1:
            return environment.clusters[0]
        index = self._prompt.select(_CLUSTER_TITLE, names)
        return environment.clusters[index]
