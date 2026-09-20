from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from rs_collector.runtime.bundle import BundleLocator

_CONFIG_DIR_NAME = "config"
_SETTINGS_FILE_NAME = "settings.yml"
_CLUSTERS_FILE_NAME = "clusters.yml"
_LOGGING_FILE_NAME = "logging.yml"
_SERVE_FILE_NAME = "copyparty.conf"
_ENV_FILE_NAME = "rsc.env"


class ConfigDirSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RSC_", extra="ignore")

    config_dir: Path | None = Field(default=None)


class ConfigPaths(BaseModel):
    model_config = ConfigDict(frozen=True)

    config_dir: Path = Field(description="Directory holding every configuration file")

    @property
    def settings_file(self) -> Path:
        return self.config_dir / _SETTINGS_FILE_NAME

    @property
    def clusters_file(self) -> Path:
        return self.config_dir / _CLUSTERS_FILE_NAME

    @property
    def logging_file(self) -> Path:
        return self.config_dir / _LOGGING_FILE_NAME

    @property
    def serve_file(self) -> Path:
        return self.config_dir / _SERVE_FILE_NAME

    @property
    def env_file(self) -> Path:
        return self.config_dir.parent / _ENV_FILE_NAME


class ConfigPathsResolver:
    def __init__(
        self,
        locator: BundleLocator | None = None,
        dir_settings: ConfigDirSettings | None = None,
    ) -> None:
        self._locator = locator or BundleLocator()
        self._dir_settings = dir_settings or ConfigDirSettings()

    def resolve(self) -> ConfigPaths:
        configured_dir = self._dir_settings.config_dir
        if configured_dir is not None:
            return ConfigPaths(config_dir=configured_dir)
        return ConfigPaths(config_dir=self._locator.root() / _CONFIG_DIR_NAME)
