from typing import Protocol

from rs_collector.jobs.registry import JobRegistry
from rs_collector.settings.models import AppSettings
from rs_collector.web.controllers.assets import AssetsController
from rs_collector.web.controllers.databases import AnalysisContext, DatabasesController
from rs_collector.web.controllers.files import FilesController
from rs_collector.web.controllers.jobs import JobsController, WorkContext
from rs_collector.web.controllers.pages import OverviewContext, PagesController
from rs_collector.web.controllers.retention import PinContext, RetentionController
from rs_collector.web.feature import WebFeature
from rs_collector.web.files.log_lines import LogReader
from rs_collector.web.files.reader import FileReader
from rs_collector.web.navigation import Navigation, Tool

_IN_THE_NAVIGATION = (PagesController, FilesController)


class ConsoleContext(OverviewContext, WorkContext, PinContext, AnalysisContext, Protocol):
    pass


class ConsoleFeatures:
    def __init__(self, context: ConsoleContext, settings: AppSettings, jobs: JobRegistry) -> None:
        self._context = context
        self._settings = settings
        self._jobs = jobs

    def navigation(self) -> Navigation:
        return Navigation(tools=self._tools())

    def all(self) -> tuple[WebFeature, ...]:
        navigation = self.navigation()
        context = self._context
        return (
            PagesController(context, self._jobs, navigation),
            JobsController(context, self._jobs, navigation),
            RetentionController(context),
            DatabasesController(context, navigation),
            self._files(navigation),
            AssetsController(),
        )

    def _files(self, navigation: Navigation) -> FilesController:
        serve = self._settings.serve
        return FilesController(
            self._settings.storage.analyses_dir,
            FileReader(serve.max_inline_bytes),
            LogReader(serve.max_log_lines),
            navigation=navigation,
        )

    def _tools(self) -> tuple[Tool, ...]:
        return tuple(feature.TOOL for feature in _IN_THE_NAVIGATION)
