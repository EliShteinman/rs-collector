import pytest
from tests.fakes import FakeSshSession

from rs_collector.exceptions.remote import RootSessionClosedError
from rs_collector.inventory.models import Cluster
from rs_collector.remote.cluster_connector import ClusterConnection
from rs_collector.remote.root_session import RootSession
from rs_collector.settings.models import AppSettings

pytestmark = pytest.mark.unit


def test_the_shell_of_an_unopened_session_is_refused(app_settings: AppSettings) -> None:
    cluster = Cluster(fqdn="c1.example.com")
    connection = ClusterConnection(cluster=cluster, host=cluster.fqdn, session=FakeSshSession())
    session = RootSession(connection, app_settings.remote)

    with pytest.raises(RootSessionClosedError):
        _ = session.shell
