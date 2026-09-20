from rs_collector.collection.collector import SupportPackageCollector
from rs_collector.concurrency.lock import CollectionLockFactory
from rs_collector.console.confirm import ConfirmPrompt
from rs_collector.console.io import ConsoleIo
from rs_collector.logging_setup.configurator import LoggerFactory
from rs_collector.packages.models import StoredPackage
from rs_collector.remote.cluster_connector import ClusterConnector
from rs_collector.remote.root_session import RootSession
from rs_collector.selection.selector import ClusterSelector
from rs_collector.settings.credentials import SshCredentials
from rs_collector.settings.models import RemoteSettings
from rs_collector.workflows.analyze import AnalyzeWorkflow

_ANALYZE_QUESTION = "Analyze this package now?"


class CollectWorkflow:
    def __init__(
        self,
        selector: ClusterSelector,
        connector: ClusterConnector,
        collector: SupportPackageCollector,
        locks: CollectionLockFactory,
        settings: RemoteSettings,
        credentials: SshCredentials,
        console: ConsoleIo,
        confirm: ConfirmPrompt,
        analyze: AnalyzeWorkflow,
    ) -> None:
        self._selector = selector
        self._connector = connector
        self._collector = collector
        self._locks = locks
        self._settings = settings
        self._credentials = credentials
        self._console = console
        self._confirm = confirm
        self._analyze = analyze
        self._logger = LoggerFactory.for_component("workflow.collect")

    def run(self) -> StoredPackage:
        cluster = self._selector.select()
        with self._locks.for_cluster(cluster.name):
            package = self._collect(cluster)
        self._console.write(f"Package stored: {package.archive_path}")
        self._offer_analysis(package)
        return package

    def _collect(self, cluster) -> StoredPackage:
        self._console.write(f"Connecting to {cluster.name} ...")
        connection = self._connector.connect(cluster)
        with RootSession(
            connection, self._settings, self._credentials.sudo_password
        ) as root_session:
            self._console.write(f"Collecting the support package through {connection.host} ...")
            return self._collector.collect(root_session)

    def _offer_analysis(self, package: StoredPackage) -> None:
        if self._confirm.ask(_ANALYZE_QUESTION, default=True):
            self._analyze.run_for(package)
