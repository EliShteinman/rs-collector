from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

_LOG_DIR_PLACEHOLDER = "{log_dir}"
_FILENAME_KEY = "filename"


class LoggingConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    version: int = Field(default=1)
    disable_existing_loggers: bool = Field(default=False)
    formatters: dict[str, Any] = Field(default_factory=dict)
    handlers: dict[str, Any] = Field(default_factory=dict)
    loggers: dict[str, Any] = Field(default_factory=dict)
    root: dict[str, Any] = Field(default_factory=dict)

    def resolved_for(self, log_dir: Path) -> dict[str, Any]:
        document = self.model_dump()
        document["handlers"] = {
            name: self._resolve_handler(handler, log_dir) for name, handler in self.handlers.items()
        }
        return document

    def file_handler_paths(self, log_dir: Path) -> list[Path]:
        return [
            Path(str(handler[_FILENAME_KEY]).replace(_LOG_DIR_PLACEHOLDER, str(log_dir)))
            for handler in self.handlers.values()
            if _FILENAME_KEY in handler
        ]

    def _resolve_handler(self, handler: dict[str, Any], log_dir: Path) -> dict[str, Any]:
        if _FILENAME_KEY not in handler:
            return handler
        resolved = dict(handler)
        resolved[_FILENAME_KEY] = str(handler[_FILENAME_KEY]).replace(
            _LOG_DIR_PLACEHOLDER, str(log_dir)
        )
        return resolved
