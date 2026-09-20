import pytest
import yaml

from rs_collector.exceptions.configuration import (
    ConfigFileFormatError,
    ConfigFileNotFoundError,
    ConfigValidationError,
)
from rs_collector.inventory.repository import CachingInventoryRepository, YamlInventoryRepository
from rs_collector.settings.paths import ConfigPaths

pytestmark = pytest.mark.unit


@pytest.fixture
def clusters_document() -> dict[str, object]:
    return {
        "environments": {
            "production": [
                {"fqdn": "c1.example.com", "nodes": ["n1.c1.example.com", "n2.c1.example.com"]}
            ],
            "staging": [{"fqdn": "c2.example.com", "nodes": ["n1.c2.example.com"]}],
        }
    }


def _write(paths: ConfigPaths, document: object) -> None:
    paths.clusters_file.write_text(yaml.safe_dump(document), encoding="utf-8")


def test_load_reads_every_environment(
    config_paths: ConfigPaths, clusters_document: dict[str, object]
) -> None:
    _write(config_paths, clusters_document)

    inventory = YamlInventoryRepository(config_paths).load()

    assert inventory.environment_names() == ("production", "staging")


def test_load_tags_each_cluster_with_its_environment(
    config_paths: ConfigPaths, clusters_document: dict[str, object]
) -> None:
    _write(config_paths, clusters_document)

    inventory = YamlInventoryRepository(config_paths).load()

    assert inventory.cluster("c2.example.com").environment == "staging"


def test_load_reads_the_nodes_of_a_cluster(
    config_paths: ConfigPaths, clusters_document: dict[str, object]
) -> None:
    _write(config_paths, clusters_document)

    inventory = YamlInventoryRepository(config_paths).load()

    assert len(inventory.cluster("c1.example.com").nodes) == 2


def test_load_rejects_a_missing_file(config_paths: ConfigPaths) -> None:
    with pytest.raises(ConfigFileNotFoundError):
        YamlInventoryRepository(config_paths).load()


def test_load_rejects_a_document_without_environments(config_paths: ConfigPaths) -> None:
    _write(config_paths, {"clusters": []})

    with pytest.raises(ConfigFileFormatError):
        YamlInventoryRepository(config_paths).load()


def test_load_rejects_an_invalid_hostname(config_paths: ConfigPaths) -> None:
    _write(config_paths, {"environments": {"production": [{"fqdn": "not a host"}]}})

    with pytest.raises(ConfigValidationError):
        YamlInventoryRepository(config_paths).load()


def test_caching_repository_reads_the_file_once(
    config_paths: ConfigPaths, clusters_document: dict[str, object]
) -> None:
    _write(config_paths, clusters_document)
    repository = CachingInventoryRepository(YamlInventoryRepository(config_paths))

    first = repository.load()

    assert repository.load() is first
