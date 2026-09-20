from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field

from rs_collector.exceptions.selection import ConnectionStringError
from rs_collector.inventory.models import Hostname

_SUPPORTED_SCHEMES = ("redis", "rediss")
_SCHEME_SEPARATOR = "://"
_PLACEHOLDER_SCHEME = "redis://"


class ConnectionTarget(BaseModel):
    model_config = ConfigDict(frozen=True)

    host: Hostname
    port: int | None = Field(default=None, gt=0, lt=65536)


class ConnectionStringParser:
    def parse(self, connection_string: str) -> ConnectionTarget:
        candidate = connection_string.strip()
        if not candidate:
            raise ConnectionStringError("The connection string is empty")
        return self._target(self._split(candidate))

    def _split(self, candidate: str) -> tuple[str, int | None]:
        parts = urlsplit(self._with_scheme(candidate))
        try:
            return self._require_host(parts.hostname), parts.port
        except ValueError as error:
            raise ConnectionStringError(f"'{candidate}' is not a valid target: {error}") from error

    def _with_scheme(self, candidate: str) -> str:
        if _SCHEME_SEPARATOR not in candidate:
            return f"{_PLACEHOLDER_SCHEME}{candidate}"
        scheme = candidate.split(_SCHEME_SEPARATOR, maxsplit=1)[0].lower()
        if scheme not in _SUPPORTED_SCHEMES:
            raise ConnectionStringError(f"Unsupported scheme '{scheme}'")
        return candidate

    def _require_host(self, host: str | None) -> str:
        if not host:
            raise ValueError("no host")
        return host

    def _target(self, parsed: tuple[str, int | None]) -> ConnectionTarget:
        host, port = parsed
        try:
            return ConnectionTarget(host=Hostname(value=host), port=port)
        except ValueError as error:
            raise ConnectionStringError(f"'{host}' is not a valid host: {error}") from error
