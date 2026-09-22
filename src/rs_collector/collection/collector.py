from datetime import UTC, datetime

from rs_collector.collection.cleanup import RemoteCleanup
from rs_collector.collection.debug_info import DebugInfoCommand
from rs_collector.collection.models import RemotePackage
from rs_collector.collection.transfer import RemoteFileTransfer
from rs_collector.exceptions.base import RsCollectorError
from rs_collector.files.digest import FileDigest
from rs_collector.logging_setup.configurator import LoggerFactory
from rs_collector.packages.models import PackageMetadata, PackageSlot, StoredPackage
from rs_collector.packages.repository import PackageRepository
from rs_collector.remote.cluster_connector import ClusterConnection
from rs_collector.remote.root_session import RootSession
from rs_collector.settings.models import RemoteSettings


class SupportPackageCollector:
    def __init__(
        self,
        repository: PackageRepository,
        settings: RemoteSettings,
        digest: FileDigest | None = None,
    ) -> None:
        self._repository = repository
        self._settings = settings
        self._digest = digest or FileDigest()
        self._logger = LoggerFactory.for_component("collection")

    def collect(self, session: RootSession) -> StoredPackage:
        connection = session.connection
        collected_at = datetime.now(UTC)
        self._logger.info(
            "Collecting a support package of %s through %s",
            connection.cluster.name,
            connection.host,
        )
        package = DebugInfoCommand(session.shell, self._settings).create_package()
        slot = self._repository.create_slot(connection.cluster.name, collected_at)
        try:
            self._fetch(session, package, slot)
        except RsCollectorError, OSError, KeyboardInterrupt:
            self._repository.discard_slot(slot)
            raise
        finally:
            RemoteCleanup(session.shell, self._settings).remove(package)
        return self._repository.save(self._metadata(connection, package, slot, collected_at))

    def _fetch(self, session: RootSession, package: RemotePackage, slot: PackageSlot) -> None:
        transfer = RemoteFileTransfer(
            session.connection.session, session.shell, self._settings, self._digest
        )
        transfer.fetch(package, slot.archive_path)

    def _metadata(
        self,
        connection: ClusterConnection,
        package: RemotePackage,
        slot: PackageSlot,
        collected_at: datetime,
    ) -> PackageMetadata:
        return PackageMetadata(
            name=slot.name,
            cluster_fqdn=connection.cluster.name,
            environment=connection.cluster.environment,
            collected_from=connection.host.value,
            collected_at=collected_at,
            original_file_name=package.file_name,
            size_bytes=package.size_bytes,
            sha256=package.sha256,
        )
