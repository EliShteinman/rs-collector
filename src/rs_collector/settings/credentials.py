from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from rs_collector.exceptions.configuration import MissingCredentialsError

_LOCAL_ENV_FILE = ".env"


class SshCredentials(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="RSC_",
        env_file=_LOCAL_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ssh_user: str = Field(default="")
    ssh_key_path: Path | None = Field(default=None)
    ssh_password: SecretStr | None = Field(default=None)
    sudo_password: SecretStr | None = Field(default=None)

    @classmethod
    def load(cls, env_file: Path | None = None) -> SshCredentials:
        files = (_LOCAL_ENV_FILE,) if env_file is None else (str(env_file), _LOCAL_ENV_FILE)
        return cls(_env_file=files)

    def require_user(self) -> str:
        if not self.ssh_user:
            raise MissingCredentialsError("RSC_SSH_USER is not set")
        return self.ssh_user

    def has_key(self) -> bool:
        return self.ssh_key_path is not None

    def has_password(self) -> bool:
        return self.ssh_password is not None

    def validated(self) -> SshCredentials:
        self.require_user()
        if not self.has_key() and not self.has_password():
            raise MissingCredentialsError("Neither RSC_SSH_KEY_PATH nor RSC_SSH_PASSWORD is set")
        return self
