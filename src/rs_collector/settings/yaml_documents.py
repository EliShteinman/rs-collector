from pathlib import Path
from typing import Any

import yaml

from rs_collector.exceptions.configuration import (
    ConfigFileFormatError,
    ConfigFileNotFoundError,
)


class YamlDocumentLoader:
    def load_mapping(self, path: Path) -> dict[str, Any]:
        document = self._read(path)
        if not isinstance(document, dict):
            raise ConfigFileFormatError(f"{path} must contain a mapping at its root")
        return document

    def _read(self, path: Path) -> Any:
        if not path.is_file():
            raise ConfigFileNotFoundError(f"Configuration file not found: {path}")
        try:
            return yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as error:
            raise ConfigFileFormatError(f"{path} is not valid YAML: {error}") from error
        except OSError as error:
            raise ConfigFileNotFoundError(f"{path} cannot be read: {error}") from error
