from pathlib import Path
from secrets import compare_digest

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from rs_collector.exceptions.configuration import MissingCredentialsError

_LOCAL_ENV_FILE = ".env"
_ENCODING = "utf-8"


class SshCredentials(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="RSC_",
        env_file=_LOCAL_ENV_FILE,
        env_file_encoding="utf-8",
        env_ignore_empty=True,
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


class WebCredentials(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="RSC_",
        env_file=_LOCAL_ENV_FILE,
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
    )

    web_user: str = Field(default="")
    web_password: SecretStr | None = Field(default=None)

    @classmethod
    def load(cls, env_file: Path | None = None) -> WebCredentials:
        files = (_LOCAL_ENV_FILE,) if env_file is None else (str(env_file), _LOCAL_ENV_FILE)
        return cls(_env_file=files)

    @property
    def demanded(self) -> bool:
        return bool(self.web_user) or self.web_password is not None

    def validated(self) -> WebCredentials:
        if self.demanded and not (self.web_user and self.web_password is not None):
            raise MissingCredentialsError(
                "RSC_WEB_USER and RSC_WEB_PASSWORD go together: "
                "set both to ask for a login, or neither to leave the web interface open"
            )
        return self

    def matches(self, user: str, password: str) -> bool:
        if self.web_password is None:
            return False
        return _same(user, self.web_user) and _same(password, self.web_password.get_secret_value())


def _same(offered: str, expected: str) -> bool:
    return compare_digest(offered.encode(_ENCODING), expected.encode(_ENCODING))
