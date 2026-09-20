import logging
import logging.config
from pathlib import Path

from pydantic import ValidationError

from rs_collector.exceptions.configuration import ConfigValidationError
from rs_collector.logging_setup.models import LoggingConfig
from rs_collector.settings.paths import ConfigPaths
from rs_collector.settings.yaml_documents import YamlDocumentLoader

_LOGGER_NAMESPACE = "rs_collector"


class LoggingConfigurator:
    def __init__(self, paths: ConfigPaths, documents: YamlDocumentLoader | None = None) -> None:
        self._paths = paths
        self._documents = documents or YamlDocumentLoader()

    def configure(self, log_dir: Path) -> None:
        config = self._load()
        self._create_log_directories(config, log_dir)
        logging.config.dictConfig(config.resolved_for(log_dir))

    def _load(self) -> LoggingConfig:
        document = self._documents.load_mapping(self._paths.logging_file)
        try:
            return LoggingConfig.model_validate(document)
        except ValidationError as error:
            raise ConfigValidationError(
                f"{self._paths.logging_file} is invalid: {error}"
            ) from error

    def _create_log_directories(self, config: LoggingConfig, log_dir: Path) -> None:
        for file_path in config.file_handler_paths(log_dir):
            file_path.parent.mkdir(parents=True, exist_ok=True)


class LoggerFactory:
    @staticmethod
    def for_component(component: str) -> logging.Logger:
        return logging.getLogger(f"{_LOGGER_NAMESPACE}.{component}")
