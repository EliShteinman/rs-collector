from rs_collector.collection.models import RemotePackage
from rs_collector.collection.output_parser import DebugInfoOutputParser
from rs_collector.exceptions.remote import RemoteCommandError
from rs_collector.logging_setup.configurator import LoggerFactory
from rs_collector.remote.root_shell import RootShell
from rs_collector.settings.models import RemoteSettings

_DEBUG_INFO_TEMPLATE = "{rladmin} cluster debug_info path {directory}"
_SIZE_TEMPLATE = "stat -c %s {path}"
_DIGEST_TEMPLATE = "sha256sum {path}"


class DebugInfoCommand:
    def __init__(
        self,
        shell: RootShell,
        settings: RemoteSettings,
        parser: DebugInfoOutputParser | None = None,
    ) -> None:
        self._shell = shell
        self._settings = settings
        self._parser = parser or DebugInfoOutputParser()
        self._logger = LoggerFactory.for_component("collection.debug_info")

    def create_package(self) -> RemotePackage:
        self._logger.info("Asking rladmin for a cluster debug info package")
        result = self._shell.run_checked(self._command(), self._settings.debug_info_timeout_seconds)
        path = self._parser.package_path(result.output)
        self._logger.info("The cluster wrote its support package to %s", path)
        return RemotePackage(
            path=path, size_bytes=self._size_of(path), sha256=self._digest_of(path)
        )

    def _command(self) -> str:
        return _DEBUG_INFO_TEMPLATE.format(
            rladmin=self._settings.rladmin_path, directory=self._settings.remote_tmp_dir
        )

    def _size_of(self, path: str) -> int:
        result = self._shell.run_checked(
            _SIZE_TEMPLATE.format(path=path), self._settings.command_timeout_seconds
        )
        size = result.first_line()
        if not size.isdigit():
            raise RemoteCommandError(f"The size of {path} could not be read: {result.output!r}")
        return int(size)

    def _digest_of(self, path: str) -> str:
        result = self._shell.run_checked(
            _DIGEST_TEMPLATE.format(path=path), self._settings.command_timeout_seconds
        )
        return result.first_line().split()[0]
