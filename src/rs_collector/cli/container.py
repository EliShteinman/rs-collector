from pathlib import Path

from rs_collector.analysis.prompt import AnalysisOptionsPrompt
from rs_collector.analysis.repository import AnalysisRepository
from rs_collector.analysis.runner import RedisScopeRunner
from rs_collector.collection.collector import SupportPackageCollector
from rs_collector.concurrency.lock import CollectionLockFactory
from rs_collector.console.choice import ChoicePrompt
from rs_collector.console.confirm import ConfirmPrompt
from rs_collector.console.io import ConsoleIo, StandardConsole
from rs_collector.inventory.repository import (
    CachingInventoryRepository,
    InventoryRepository,
    YamlInventoryRepository,
)
from rs_collector.logging_setup.configurator import LoggingConfigurator
from rs_collector.packages.repository import PackageRepository
from rs_collector.packages.selector import InteractivePackageSelector
from rs_collector.remote.cluster_connector import ClusterConnector
from rs_collector.remote.connector import ParamikoHostConnector
from rs_collector.retention.cleaner import RetentionCleaner
from rs_collector.retention.pin import PinService
from rs_collector.retention.policy import RetentionPolicy
from rs_collector.selection.connection_string import ConnectionStringParser
from rs_collector.selection.connection_string_selector import ConnectionStringClusterSelector
from rs_collector.selection.interactive import InteractiveClusterSelector
from rs_collector.selection.resolver import ClusterResolver
from rs_collector.selection.selector import ClusterSelector
from rs_collector.serve.server import DisplayServer
from rs_collector.settings.credentials import SshCredentials
from rs_collector.settings.loader import SettingsLoader
from rs_collector.settings.models import AppSettings
from rs_collector.settings.paths import ConfigPaths, ConfigPathsResolver
from rs_collector.workflows.analyze import AnalyzeWorkflow
from rs_collector.workflows.collect import CollectWorkflow

_LOG_DIR_NAME = "logs"


class Container:
    def __init__(self, paths: ConfigPaths | None = None, console: ConsoleIo | None = None) -> None:
        self._paths = paths or ConfigPathsResolver().resolve()
        self._console = console or StandardConsole()
        self._settings = SettingsLoader(self._paths).load()
        self._credentials = SshCredentials()
        self._inventory: InventoryRepository = CachingInventoryRepository(
            YamlInventoryRepository(self._paths)
        )

    def configure_logging(self) -> None:
        LoggingConfigurator(self._paths).configure(self.log_dir)

    @property
    def settings(self) -> AppSettings:
        return self._settings

    @property
    def console(self) -> ConsoleIo:
        return self._console

    @property
    def log_dir(self) -> Path:
        return self._settings.storage.data_root / _LOG_DIR_NAME

    def packages(self) -> PackageRepository:
        return PackageRepository(self._settings.storage)

    def analyses(self) -> AnalysisRepository:
        return AnalysisRepository(self._settings.storage)

    def pins(self) -> PinService:
        return PinService(self.packages(), self.analyses())

    def cleaner(self) -> RetentionCleaner:
        return RetentionCleaner(
            self.packages(),
            self.analyses(),
            RetentionPolicy(max_age_days=self._settings.retention.max_age_days),
        )

    def display_server(self) -> DisplayServer:
        return DisplayServer(self._settings.serve, self._settings.storage, self._paths.serve_file)

    def analyze_workflow(self) -> AnalyzeWorkflow:
        return AnalyzeWorkflow(
            InteractivePackageSelector(self.packages(), ChoicePrompt(self._console)),
            AnalysisOptionsPrompt(self._console),
            RedisScopeRunner(self.analyses(), self._settings.analysis, self._settings.storage),
            self._console,
        )

    def collect_workflow(self, connection_string: str | None = None) -> CollectWorkflow:
        return CollectWorkflow(
            self._cluster_selector(connection_string),
            ClusterConnector(ParamikoHostConnector(self._credentials, self._settings.remote)),
            SupportPackageCollector(self.packages(), self._settings.remote),
            CollectionLockFactory(self._settings.storage.locks_dir),
            self._settings.remote,
            self._credentials,
            self._console,
            ConfirmPrompt(self._console),
            self.analyze_workflow(),
        )

    def _cluster_selector(self, connection_string: str | None) -> ClusterSelector:
        if connection_string is None:
            return InteractiveClusterSelector(self._inventory, ChoicePrompt(self._console))
        return ConnectionStringClusterSelector(
            connection_string, self._inventory, ConnectionStringParser(), ClusterResolver()
        )
