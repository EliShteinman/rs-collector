import pytest
from tests.fakes import FakeHostConnector, FakeSshSession

from rs_collector.exceptions.remote import ClusterUnreachableError
from rs_collector.inventory.models import Cluster
from rs_collector.remote.cluster_connector import ClusterConnector

pytestmark = pytest.mark.unit


@pytest.fixture
def cluster() -> Cluster:
    return Cluster.model_validate(
        {"fqdn": "c1.example.com", "nodes": ["n1.c1.example.com", "n2.c1.example.com"]}
    )


def test_connect_prefers_the_cluster_fqdn(cluster: Cluster) -> None:
    connector = FakeHostConnector({"c1.example.com": FakeSshSession()})

    connection = ClusterConnector(connector).connect(cluster)

    assert connection.host.value == "c1.example.com"


def test_connect_falls_back_to_the_next_node(cluster: Cluster) -> None:
    connector = FakeHostConnector({"n2.c1.example.com": FakeSshSession()})

    connection = ClusterConnector(connector).connect(cluster)

    assert connection.host.value == "n2.c1.example.com"


def test_connect_tries_the_hosts_in_order(cluster: Cluster) -> None:
    connector = FakeHostConnector({"n2.c1.example.com": FakeSshSession()})

    ClusterConnector(connector).connect(cluster)

    assert connector.attempts == [
        "c1.example.com",
        "n1.c1.example.com",
        "n2.c1.example.com",
    ]


def test_connect_reports_every_failure(cluster: Cluster) -> None:
    connector = FakeHostConnector({})

    with pytest.raises(ClusterUnreachableError):
        ClusterConnector(connector).connect(cluster)
