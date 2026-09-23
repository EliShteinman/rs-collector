from rs_collector.collection.collector import SupportPackageCollector
from rs_collector.concurrency.lock import CollectionLockFactory
from rs_collector.console.io import ConsoleIo
from rs_collector.inventory.models import Cluster
from rs_collector.logging_setup.configurator import LoggerFactory
from rs_collector.packages.models import StoredPackage
from rs_collector.remote.cluster_connector import ClusterConnector
from rs_collector.remote.root_session import RootSession
from rs_collector.settings.credentials import SshCredentials
from rs_collector.settings.models import RemoteSettings


class CollectWorkflow:
    def __init__(
        self,
        connector: ClusterConnector,
        collector: SupportPackageCollector,
        locks: CollectionLockFactory,
        settings: RemoteSettings,
        credentials: SshCredentials,
        console: ConsoleIo,
    ) -> None:
        self._connector = connector
        self._collector = collector
        self._locks = locks
        self._settings = settings
        self._credentials = credentials
        self._console = console
        self._logger = LoggerFactory.for_component("workflow.collect")

    def run_for(self, cluster: Cluster) -> StoredPackage:
        self._logger.info("Collecting a support package of %s", cluster.name)
        with self._locks.for_cluster(cluster.name):
            package = self._collect(cluster)
        self._console.write(f"Package stored: {package.archive_path}")
        self._logger.info("The package of %s is stored as %s", cluster.name, package.name)
        return package

    def _collect(self, cluster: Cluster) -> StoredPackage:
        self._console.write(f"Connecting to {cluster.name} ...")
        connection = self._connector.connect(cluster)
        with RootSession(
            connection, self._settings, self._credentials.sudo_password
        ) as root_session:
            self._console.write(f"Collecting the support package through {connection.host} ...")
            return self._collector.collect(root_session)
