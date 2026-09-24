from typing import Protocol, Self

from rs_collector.analysis.repository import AnalysisRepository
from rs_collector.console.io import ConsoleIo
from rs_collector.inventory.repository import InventoryRepository
from rs_collector.packages.repository import PackageRepository
from rs_collector.retention.pin import PinService
from rs_collector.settings.models import AppSettings
from rs_collector.status.service import StatusService
from rs_collector.web.security.access import AccessGuard
from rs_collector.workflows.analyze import AnalyzeWorkflow
from rs_collector.workflows.collect import CollectWorkflow


class WebContext(Protocol):
    @property
    def settings(self) -> AppSettings: ...

    def with_console(self, console: ConsoleIo) -> Self: ...

    def inventory(self) -> InventoryRepository: ...

    def packages(self) -> PackageRepository: ...

    def analyses(self) -> AnalysisRepository: ...

    def pins(self) -> PinService: ...

    def status(self) -> StatusService: ...

    def access_guard(self) -> AccessGuard: ...

    def collect_workflow(self) -> CollectWorkflow: ...

    def analyze_workflow(self) -> AnalyzeWorkflow: ...
