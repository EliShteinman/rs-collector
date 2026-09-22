from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from rs_collector.exceptions.configuration import MissingSettingError

_LOCAL_ENV_FILE = ".env"


class EnvironmentSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="RSC_",
        env_file=_LOCAL_ENV_FILE,
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
    )

    data_root: Path | None = Field(default=None)

    @classmethod
    def load(cls, env_file: Path | None = None) -> EnvironmentSettings:
        files = (_LOCAL_ENV_FILE,) if env_file is None else (str(env_file), _LOCAL_ENV_FILE)
        return cls(_env_file=files)

    def require_data_root(self) -> Path:
        if self.data_root is None:
            raise MissingSettingError("RSC_DATA_ROOT is not set: the directory all output goes to")
        return self.data_root.expanduser()
