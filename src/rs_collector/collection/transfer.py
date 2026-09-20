from pathlib import Path

from rs_collector.collection.models import RemotePackage
from rs_collector.exceptions.remote import TransferIntegrityError
from rs_collector.files.digest import FileDigest
from rs_collector.logging_setup.configurator import LoggerFactory
from rs_collector.remote.root_shell import RootShell
from rs_collector.remote.session import SshSession
from rs_collector.settings.models import RemoteSettings

_READABLE_TEMPLATE = "chmod 0644 {path}"


class RemoteFileTransfer:
    def __init__(
        self,
        session: SshSession,
        shell: RootShell,
        settings: RemoteSettings,
        digest: FileDigest | None = None,
    ) -> None:
        self._session = session
        self._shell = shell
        self._settings = settings
        self._digest = digest or FileDigest()
        self._logger = LoggerFactory.for_component("collection.transfer")

    def fetch(self, package: RemotePackage, destination: Path) -> Path:
        self._make_readable(package)
        self._session.download(package.path, destination)
        self._verify(package, destination)
        self._logger.info("%s arrived as %s", package.file_name, destination)
        return destination

    def _make_readable(self, package: RemotePackage) -> None:
        self._shell.run_checked(
            _READABLE_TEMPLATE.format(path=package.path), self._settings.command_timeout_seconds
        )

    def _verify(self, package: RemotePackage, destination: Path) -> None:
        local_size = destination.stat().st_size
        if local_size != package.size_bytes:
            raise TransferIntegrityError(
                f"{destination} has {local_size} bytes, the cluster reported {package.size_bytes}"
            )
        local_digest = self._digest.of(destination)
        if local_digest != package.sha256:
            raise TransferIntegrityError(
                f"{destination} has checksum {local_digest}, the cluster reported {package.sha256}"
            )
