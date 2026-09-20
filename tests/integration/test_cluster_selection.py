import pytest
import yaml

from rs_collector.inventory.repository import YamlInventoryRepository
from rs_collector.selection.connection_string import ConnectionStringParser
from rs_collector.selection.connection_string_selector import ConnectionStringClusterSelector
from rs_collector.selection.resolver import ClusterResolver
from rs_collector.settings.paths import ConfigPaths

pytestmark = pytest.mark.integration


@pytest.fixture
def populated_config(config_paths: ConfigPaths) -> ConfigPaths:
    document = {
        "environments": {
            "production": [
                {"fqdn": "c1.example.com", "nodes": ["n1.c1.example.com"]},
                {"fqdn": "c2.example.com", "nodes": ["n1.c2.example.com"]},
            ]
        }
    }
    config_paths.clusters_file.write_text(yaml.safe_dump(document), encoding="utf-8")
    return config_paths


def _selector(paths: ConfigPaths, connection_string: str) -> ConnectionStringClusterSelector:
    return ConnectionStringClusterSelector(
        connection_string,
        YamlInventoryRepository(paths),
        ConnectionStringParser(),
        ClusterResolver(),
    )


def test_connection_string_selects_the_matching_cluster(populated_config: ConfigPaths) -> None:
    selector = _selector(populated_config, "redis://user:pw@mydb.c2.example.com:12000")

    assert selector.select().name == "c2.example.com"


def test_selected_cluster_carries_its_environment(populated_config: ConfigPaths) -> None:
    selector = _selector(populated_config, "n1.c1.example.com")

    assert selector.select().environment == "production"


def test_shipped_inventory_resolves_its_own_clusters(repo_config_paths: ConfigPaths) -> None:
    selector = _selector(repo_config_paths, "redis://db.cluster1.example.com:12000")

    assert selector.select().name == "cluster1.example.com"
