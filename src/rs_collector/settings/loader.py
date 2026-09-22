from typing import Any

from pydantic import ValidationError

from rs_collector.exceptions.configuration import ConfigValidationError
from rs_collector.settings.environment import EnvironmentSettings
from rs_collector.settings.models import AppSettings
from rs_collector.settings.paths import ConfigPaths
from rs_collector.settings.yaml_documents import YamlDocumentLoader

_STORAGE_SECTION = "storage"
_DATA_ROOT_KEY = "data_root"


class SettingsLoader:
    def __init__(
        self,
        paths: ConfigPaths,
        documents: YamlDocumentLoader | None = None,
        environment: EnvironmentSettings | None = None,
    ) -> None:
        self._paths = paths
        self._documents = documents or YamlDocumentLoader()
        self._environment = environment or EnvironmentSettings.load(paths.env_file)

    def load(self) -> AppSettings:
        document = self._with_data_root(self._documents.load_mapping(self._paths.settings_file))
        try:
            return AppSettings.model_validate(document)
        except ValidationError as error:
            raise ConfigValidationError(
                f"{self._paths.settings_file} is invalid: {error}"
            ) from error

    def _with_data_root(self, document: dict[str, Any]) -> dict[str, Any]:
        storage = dict(document.get(_STORAGE_SECTION) or {})
        storage[_DATA_ROOT_KEY] = self._environment.require_data_root()
        return {**document, _STORAGE_SECTION: storage}
