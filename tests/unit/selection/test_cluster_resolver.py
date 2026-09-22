import pytest

from rs_collector.exceptions.selection import ClusterNotFoundError
from rs_collector.inventory.models import Hostname, Inventory
from rs_collector.selection.resolver import ClusterResolver

pytestmark = pytest.mark.unit


@pytest.fixture
def inventory() -> Inventory:
    return Inventory.model_validate(
        {
            "environments": [
                {
                    "name": "production",
                    "clusters": [
                        {"fqdn": "example.com"},
                        {"fqdn": "c1.example.com", "nodes": ["n1.c1.example.com"]},
                    ],
                }
            ]
        }
    )


@pytest.fixture
def resolver() -> ClusterResolver:
    return ClusterResolver()


def test_resolve_matches_the_fqdn(resolver: ClusterResolver, inventory: Inventory) -> None:
    cluster = resolver.resolve(Hostname(value="c1.example.com"), inventory)

    assert cluster.name == "c1.example.com"


def test_resolve_matches_a_database_subdomain(
    resolver: ClusterResolver, inventory: Inventory
) -> None:
    cluster = resolver.resolve(Hostname(value="mydb.c1.example.com"), inventory)

    assert cluster.name == "c1.example.com"


def test_resolve_matches_a_node(resolver: ClusterResolver, inventory: Inventory) -> None:
    cluster = resolver.resolve(Hostname(value="n1.c1.example.com"), inventory)

    assert cluster.name == "c1.example.com"


def test_resolve_rejects_an_unknown_host(resolver: ClusterResolver, inventory: Inventory) -> None:
    with pytest.raises(ClusterNotFoundError):
        resolver.resolve(Hostname(value="other.internal"), inventory)
