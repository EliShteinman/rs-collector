import json
from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from rs_collector.logging_setup.configurator import LoggerFactory
from rs_collector.retention.cleaner import CleanupReport
from rs_collector.settings.models import StorageSettings

_ENCODING = "utf-8"
_JSON_INDENT = 2


class CleanupRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    finished_at: datetime
    removed_packages: int = Field(ge=0)
    removed_analyses: int = Field(ge=0)


class CleanupHistory:
    def __init__(self, settings: StorageSettings) -> None:
        self._settings = settings
        self._logger = LoggerFactory.for_component("retention.history")

    def record(self, report: CleanupReport, finished_at: datetime | None = None) -> CleanupRecord:
        written = CleanupRecord(
            finished_at=finished_at or datetime.now(UTC),
            removed_packages=len(report.removed_packages),
            removed_analyses=len(report.removed_analyses),
        )
        path = self._settings.cleanup_history_file
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(written.model_dump_json(indent=_JSON_INDENT), encoding=_ENCODING)
        return written

    def last(self) -> CleanupRecord | None:
        path = self._settings.cleanup_history_file
        try:
            return CleanupRecord.model_validate_json(path.read_text(encoding=_ENCODING))
        except FileNotFoundError:
            return None
        except (OSError, ValidationError, json.JSONDecodeError) as error:
            self._logger.warning("%s cannot be read: %s", path, error)
            return None
