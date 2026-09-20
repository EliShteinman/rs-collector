from typing import Any, Protocol

from pydantic import ValidationError

from rs_collector.exceptions.configuration import (
    ConfigFileFormatError,
    ConfigValidationError,
)
from rs_collector.inventory.models import Environment, Inventory
from rs_collector.logging_setup.configurator import LoggerFactory
from rs_collector.settings.paths import ConfigPaths
from rs_collector.settings.yaml_documents import YamlDocumentLoader

_ENVIRONMENTS_KEY = "environments"


class InventoryRepository(Protocol):
    def load(self) -> Inventory: ...


class YamlInventoryRepository:
    def __init__(self, paths: ConfigPaths, documents: YamlDocumentLoader | None = None) -> None:
        self._paths = paths
        self._documents = documents or YamlDocumentLoader()
        self._logger = LoggerFactory.for_component("inventory")

    def load(self) -> Inventory:
        document = self._documents.load_mapping(self._paths.clusters_file)
        inventory = self._build(self._environments_section(document))
        self._logger.debug(
            "Loaded %d clusters from %s", len(inventory.clusters), self._paths.clusters_file
        )
        return inventory

    def _environments_section(self, document: dict[str, Any]) -> dict[str, Any]:
        section = document.get(_ENVIRONMENTS_KEY)
        if not isinstance(section, dict):
            raise ConfigFileFormatError(
                f"{self._paths.clusters_file} must hold an '{_ENVIRONMENTS_KEY}' mapping"
            )
        return section

    def _build(self, section: dict[str, Any]) -> Inventory:
        try:
            environments = tuple(
                self._environment(name, clusters) for name, clusters in section.items()
            )
            return Inventory(environments=environments)
        except ValidationError as error:
            raise ConfigValidationError(
                f"{self._paths.clusters_file} is invalid: {error}"
            ) from error

    def _environment(self, name: str, clusters: Any) -> Environment:
        environment = Environment.model_validate({"name": name, "clusters": clusters})
        return environment.model_copy(
            update={
                "clusters": tuple(
                    cluster.with_environment(name) for cluster in environment.clusters
                )
            }
        )


class CachingInventoryRepository:
    def __init__(self, repository: InventoryRepository) -> None:
        self._repository = repository
        self._cached: Inventory | None = None

    def load(self) -> Inventory:
        if self._cached is None:
            self._cached = self._repository.load()
        return self._cached
