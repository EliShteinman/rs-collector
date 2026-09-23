from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import parse_qs

_ENCODING = "utf-8"
_HTML = "text/html; charset=utf-8"
_JSON = "application/json"
_FORWARDED_PREFIX = "x-forwarded-prefix"


@dataclass(frozen=True, slots=True)
class Request:
    method: str
    path: str
    query: Mapping[str, str] = field(default_factory=dict)
    form: Mapping[str, str] = field(default_factory=dict)
    headers: Mapping[str, str] = field(default_factory=dict)
    base_path: str = ""

    @classmethod
    def parse(
        cls,
        method: str,
        path: str,
        query_string: str = "",
        body: bytes = b"",
        headers: Mapping[str, str] | None = None,
        base_path: str = "",
    ) -> Request:
        lowered = {name.lower(): value for name, value in (headers or {}).items()}
        return cls(
            method=method,
            path=path,
            query=_single_values(query_string),
            form=_single_values(body.decode(_ENCODING, errors="replace")),
            headers=lowered,
            base_path=lowered.get(_FORWARDED_PREFIX, base_path).rstrip("/"),
        )

    def url(self, path: str) -> str:
        return f"{self.base_path}{path}"


def _single_values(encoded: str) -> dict[str, str]:
    return {name: values[0] for name, values in parse_qs(encoded, keep_blank_values=True).items()}


@dataclass(frozen=True, slots=True)
class Response:
    status: int = 200
    body: bytes = b""
    content_type: str = _HTML
    headers: Mapping[str, str] = field(default_factory=dict)
    source: Path | None = None
    length: int | None = None

    @classmethod
    def html(cls, markup: str, status: int = 200) -> Response:
        return cls(status=status, body=markup.encode(_ENCODING), content_type=_HTML)

    @classmethod
    def json(cls, payload: str, status: int = 200) -> Response:
        return cls(status=status, body=payload.encode(_ENCODING), content_type=_JSON)

    @classmethod
    def redirect(cls, location: str) -> Response:
        return cls(status=303, headers={"Location": location})

    @classmethod
    def file(cls, content: bytes, content_type: str) -> Response:
        return cls(status=200, body=content, content_type=content_type)

    @classmethod
    def stream(cls, path: Path, content_type: str) -> Response:
        return cls(status=200, content_type=content_type, source=path, length=path.stat().st_size)

    def size(self) -> int:
        return self.length if self.length is not None else len(self.body)

    def chunks(self, chunk_size: int) -> Iterator[bytes]:
        if self.source is None:
            yield self.body
            return
        with self.source.open("rb") as stream:
            while chunk := stream.read(chunk_size):
                yield chunk

    def payload(self) -> bytes:
        return self.source.read_bytes() if self.source is not None else self.body
