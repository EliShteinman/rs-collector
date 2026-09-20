import pytest
from pydantic import ValidationError

from rs_collector.inventory.models import Cluster, Environment, Hostname, Inventory

pytestmark = pytest.mark.unit


def test_hostname_is_lowercased() -> None:
    assert Hostname(value="Cluster1.Example.COM").value == "cluster1.example.com"


def test_hostname_drops_the_trailing_dot() -> None:
    assert Hostname(value="cluster1.example.com.").value == "cluster1.example.com"


@pytest.mark.parametrize("value", ["", " ", "bad_host", "-leading.example.com", "a..b"])
def test_hostname_rejects_invalid_values(value: str) -> None:
    with pytest.raises(ValidationError):
        Hostname(value=value)


def test_cluster_connects_to_the_fqdn_first() -> None:
    cluster = Cluster.model_validate({"fqdn": "c1.example.com", "nodes": ["n1.c1.example.com"]})

    assert cluster.hosts_in_connection_order()[0].value == "c1.example.com"


def test_cluster_rejects_a_duplicated_node() -> None:
    with pytest.raises(ValidationError):
        Cluster.model_validate(
            {"fqdn": "c1.example.com", "nodes": ["n1.c1.example.com", "n1.c1.example.com"]}
        )


def test_environment_requires_at_least_one_cluster() -> None:
    with pytest.raises(ValidationError):
        Environment.model_validate({"name": "production", "clusters": []})


def test_environment_rejects_a_duplicated_cluster() -> None:
    with pytest.raises(ValidationError):
        Environment.model_validate(
            {
                "name": "production",
                "clusters": [{"fqdn": "c1.example.com"}, {"fqdn": "c1.example.com"}],
            }
        )


def test_inventory_finds_a_cluster_by_fqdn() -> None:
    inventory = Inventory.model_validate(
        {"environments": [{"name": "production", "clusters": [{"fqdn": "c1.example.com"}]}]}
    )

    assert inventory.cluster("C1.EXAMPLE.COM") is not None


def test_inventory_returns_none_for_an_unknown_cluster() -> None:
    assert Inventory().cluster("c9.example.com") is None


def test_empty_inventory_is_reported_as_empty() -> None:
    assert Inventory().is_empty()
