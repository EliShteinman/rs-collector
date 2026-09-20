from pydantic import ValidationError

from rs_collector.exceptions.configuration import ConfigValidationError
from rs_collector.settings.models import AppSettings
from rs_collector.settings.paths import ConfigPaths
from rs_collector.settings.yaml_documents import YamlDocumentLoader


class SettingsLoader:
    def __init__(self, paths: ConfigPaths, documents: YamlDocumentLoader | None = None) -> None:
        self._paths = paths
        self._documents = documents or YamlDocumentLoader()

    def load(self) -> AppSettings:
        document = self._documents.load_mapping(self._paths.settings_file)
        try:
            return AppSettings.model_validate(document)
        except ValidationError as error:
            raise ConfigValidationError(
                f"{self._paths.settings_file} is invalid: {error}"
            ) from error
