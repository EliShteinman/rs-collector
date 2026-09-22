import shlex

from rs_collector.collection.models import RemotePackage
from rs_collector.exceptions.remote import RemoteCommandError, RemoteCommandTimeoutError
from rs_collector.logging_setup.configurator import LoggerFactory
from rs_collector.remote.root_shell import RootShell
from rs_collector.settings.models import RemoteSettings

_REMOVE_TEMPLATE = "rm -f {path}"


class RemoteCleanup:
    def __init__(self, shell: RootShell, settings: RemoteSettings) -> None:
        self._shell = shell
        self._settings = settings
        self._logger = LoggerFactory.for_component("collection.cleanup")

    def remove(self, package: RemotePackage) -> None:
        self._logger.debug("Removing %s from the cluster", package.path)
        try:
            self._shell.run_checked(
                _REMOVE_TEMPLATE.format(path=shlex.quote(package.path)),
                self._settings.command_timeout_seconds,
            )
        except (RemoteCommandError, RemoteCommandTimeoutError) as error:
            self._logger.error("%s stayed behind on the cluster: %s", package.path, error)
            return
        self._logger.info("%s was removed from the cluster", package.path)
