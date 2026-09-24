import json
import shutil
from pathlib import Path

from pydantic import ValidationError

from rs_collector.analysis.models import AnalysisMetadata, StoredAnalysis
from rs_collector.exceptions.storage import AnalysisNotFoundError, MetadataError
from rs_collector.logging_setup.configurator import LoggerFactory
from rs_collector.settings.models import StorageSettings

_ENCODING = "utf-8"
_JSON_INDENT = 2


class AnalysisRepository:
    def __init__(self, settings: StorageSettings) -> None:
        self._settings = settings
        self._logger = LoggerFactory.for_component("analysis.repository")

    def create(self, metadata: AnalysisMetadata) -> StoredAnalysis:
        directory = self._settings.analyses_dir / metadata.name
        directory.mkdir(parents=True, exist_ok=True)
        self._logger.info("Created the analysis directory %s", directory)
        return self.save(metadata)

    def save(self, metadata: AnalysisMetadata) -> StoredAnalysis:
        directory = self._settings.analyses_dir / metadata.name
        directory.mkdir(parents=True, exist_ok=True)
        self._metadata_path(directory).write_text(
            metadata.model_dump_json(indent=_JSON_INDENT), encoding=_ENCODING
        )
        return StoredAnalysis(metadata=metadata, directory=directory)

    def get(self, name: str) -> StoredAnalysis:
        directory = self._settings.analyses_dir / name
        if not self._metadata_path(directory).is_file():
            raise AnalysisNotFoundError(f"No analysis named '{name}' is stored")
        return StoredAnalysis(metadata=self._read_metadata(directory), directory=directory)

    def list(self) -> tuple[StoredAnalysis, ...]:
        if not self._settings.analyses_dir.is_dir():
            return ()
        analyses = (self._readable(directory) for directory in self._analysis_directories())
        return tuple(
            sorted(
                (analysis for analysis in analyses if analysis is not None),
                key=lambda item: item.metadata.analyzed_at,
                reverse=True,
            )
        )

    def _readable(self, directory: Path) -> StoredAnalysis | None:
        try:
            return StoredAnalysis(metadata=self._read_metadata(directory), directory=directory)
        except MetadataError as error:
            self._logger.warning("Skipping an unreadable analysis: %s", error)
            return None

    def names(self) -> tuple[str, ...]:
        if not self._settings.analyses_dir.is_dir():
            return ()
        return tuple(
            directory.name
            for directory in self._settings.analyses_dir.iterdir()
            if directory.is_dir()
        )

    def delete(self, name: str) -> None:
        stored = self.get(name)
        shutil.rmtree(stored.directory)
        self._logger.warning("Deleted the analysis %s", name)

    def _analysis_directories(self) -> tuple[Path, ...]:
        return tuple(
            directory
            for directory in self._settings.analyses_dir.iterdir()
            if self._metadata_path(directory).is_file()
        )

    def _metadata_path(self, directory: Path) -> Path:
        return directory / self._settings.analysis_metadata_name

    def _read_metadata(self, directory: Path) -> AnalysisMetadata:
        path = self._metadata_path(directory)
        try:
            return AnalysisMetadata.model_validate_json(path.read_text(encoding=_ENCODING))
        except (OSError, ValidationError, json.JSONDecodeError) as error:
            raise MetadataError(f"{path} cannot be read: {error}") from error
