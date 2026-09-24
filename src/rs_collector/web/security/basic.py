from base64 import b64decode
from collections.abc import Mapping
from dataclasses import dataclass

_AUTHORIZATION = "authorization"
_SCHEME = "basic"
_SEPARATOR = ":"
_ENCODING = "utf-8"


@dataclass(frozen=True, slots=True)
class BasicLogin:
    user: str
    password: str

    @classmethod
    def offered(cls, headers: Mapping[str, str]) -> BasicLogin | None:
        scheme, _, encoded = headers.get(_AUTHORIZATION, "").partition(" ")
        if scheme.lower() != _SCHEME or not encoded:
            return None
        return cls._decoded(encoded.strip())

    @classmethod
    def _decoded(cls, encoded: str) -> BasicLogin | None:
        try:
            pair = b64decode(encoded, validate=True).decode(_ENCODING)
        except ValueError:
            return None
        user, separator, password = pair.partition(_SEPARATOR)
        if not separator:
            return None
        return cls(user=user, password=password)
