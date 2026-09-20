import json
import shutil
from datetime import datetime
from pathlib import Path

from pydantic import ValidationError

from rs_collector.exceptions.storage import MetadataError, PackageNotFoundError
from rs_collector.logging_setup.configurator import LoggerFactory
from rs_collector.packages.models import PackageMetadata, PackageSlot, StoredPackage
from rs_collector.packages.namer import PackageNamer
from rs_collector.settings.models import StorageSettings

_ENCODING = "utf-8"
_JSON_INDENT = 2


class PackageRepository:
    def __init__(self, settings: StorageSettings, namer: PackageNamer | None = None) -> None:
        self._settings = settings
        self._namer = namer or PackageNamer()
        self._logger = LoggerFactory.for_component("packages")

    def create_slot(self, cluster_fqdn: str, collected_at: datetime) -> PackageSlot:
        name = self._namer.name_for(cluster_fqdn, collected_at)
        directory = self._settings.packages_dir / name
        directory.mkdir(parents=True, exist_ok=True)
        self._logger.debug("Prepared the package directory %s", directory)
        return PackageSlot(
            name=name,
            directory=directory,
            archive_path=directory / self._settings.package_archive_name,
        )

    def save(self, metadata: PackageMetadata) -> StoredPackage:
        directory = self._settings.packages_dir / metadata.name
        directory.mkdir(parents=True, exist_ok=True)
        self._metadata_path(directory).write_text(
            metadata.model_dump_json(indent=_JSON_INDENT), encoding=_ENCODING
        )
        self._logger.info("Stored the package %s", metadata.name)
        return self._stored(directory, metadata)

    def get(self, name: str) -> StoredPackage:
        directory = self._settings.packages_dir / name
        if not directory.is_dir():
            raise PackageNotFoundError(f"No package named '{name}' is stored")
        return self._stored(directory, self._read_metadata(directory))

    def list(self) -> tuple[StoredPackage, ...]:
        if not self._settings.packages_dir.is_dir():
            return ()
        return tuple(
            sorted(
                (self._stored(d, self._read_metadata(d)) for d in self._package_directories()),
                key=lambda package: package.metadata.collected_at,
                reverse=True,
            )
        )

    def delete(self, name: str) -> None:
        stored = self.get(name)
        shutil.rmtree(stored.directory)
        self._logger.warning("Deleted the package %s", name)

    def _package_directories(self) -> tuple[Path, ...]:
        return tuple(
            directory
            for directory in self._settings.packages_dir.iterdir()
            if self._metadata_path(directory).is_file()
        )

    def _stored(self, directory: Path, metadata: PackageMetadata) -> StoredPackage:
        return StoredPackage(
            metadata=metadata,
            directory=directory,
            archive_path=directory / self._settings.package_archive_name,
        )

    def _metadata_path(self, directory: Path) -> Path:
        return directory / self._settings.package_metadata_name

    def _read_metadata(self, directory: Path) -> PackageMetadata:
        path = self._metadata_path(directory)
        try:
            return PackageMetadata.model_validate_json(path.read_text(encoding=_ENCODING))
        except (OSError, ValidationError, json.JSONDecodeError) as error:
            raise MetadataError(f"{path} cannot be read: {error}") from error
