import gzip
from pathlib import Path

from rs_collector.exceptions.storage import ArtifactNotFoundError
from rs_collector.logging_setup.configurator import LoggerFactory
from rs_collector.web.files import media

_ENCODING = "utf-8"
_TRUNCATION_NOTE = (
    "... showing the last {shown} bytes of {total}. Add ?raw=1 to the address for the whole file.\n"
)


class FileReader:
    def __init__(self, max_inline_bytes: int) -> None:
        self._max_inline_bytes = max_inline_bytes
        self._logger = LoggerFactory.for_component("web.files")

    def read(self, path: Path, raw: bool = False) -> tuple[bytes, str]:
        if raw or not media.is_readable_text(path):
            return self._bytes(path), self._raw_type(path, raw)
        return self._text(path), media.content_type(path)

    def _raw_type(self, path: Path, raw: bool) -> str:
        if raw and media.is_compressed(path):
            return "application/gzip"
        return media.content_type(path)

    def _bytes(self, path: Path) -> bytes:
        try:
            return path.read_bytes()
        except OSError as error:
            raise ArtifactNotFoundError(f"{path.name} cannot be read: {error}") from error

    def _text(self, path: Path) -> bytes:
        content = self._decompressed(path) if media.is_compressed(path) else self._bytes(path)
        if len(content) <= self._max_inline_bytes:
            return content
        self._logger.debug("Showing the tail of %s (%d bytes)", path, len(content))
        note = _TRUNCATION_NOTE.format(shown=self._max_inline_bytes, total=len(content))
        return note.encode(_ENCODING) + content[-self._max_inline_bytes :]

    def _decompressed(self, path: Path) -> bytes:
        try:
            with gzip.open(path, "rb") as stream:
                return stream.read()
        except (OSError, EOFError) as error:
            raise ArtifactNotFoundError(
                f"{path.name} is not a readable archive: {error}"
            ) from error
