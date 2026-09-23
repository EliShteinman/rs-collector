from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path

from rs_collector.exceptions.storage import ArtifactNotFoundError
from rs_collector.logging_setup.configurator import LoggerFactory
from rs_collector.web.files import media
from rs_collector.web.files.reader import FileReader
from rs_collector.web.http import Request, Response
from rs_collector.web.views import listing

_ANALYSES_PATH = "/analyses/"
_RAW_FLAG = "raw"
_LIST_FLAG = "list"
_TRUTHY = ("1", "yes", "true")
_INDEX_NAMES = ("index.html",)
_SLASH = "/"


class FilesController:
    def __init__(self, root: Path, reader: FileReader, heading: str = "Analyses") -> None:
        self._root = root
        self._reader = reader
        self._heading = heading
        self._logger = LoggerFactory.for_component("web.files")

    def serve(self, request: Request, parameters: Mapping[str, str]) -> Response:
        relative = parameters.get("path", "").strip("/")
        target = self._resolved(relative)
        if target.is_dir():
            if not request.path.endswith(_SLASH):
                return Response.redirect(request.url(f"{_ANALYSES_PATH}{relative}{_SLASH}"))
            return self._directory(request, target, relative)
        if target.is_file():
            body, content_type = self._reader.read(target, raw=_wants_raw(request))
            return Response.file(body, content_type)
        raise ArtifactNotFoundError(f"{_ANALYSES_PATH}{relative} does not exist")

    def _resolved(self, relative: str) -> Path:
        root = self._root.resolve()
        target = (root / relative).resolve()
        if target != root and root not in target.parents:
            self._logger.warning("Refused a path outside %s: %s", root, relative)
            raise ArtifactNotFoundError(f"{_ANALYSES_PATH}{relative} does not exist")
        return target

    def _directory(self, request: Request, target: Path, relative: str) -> Response:
        index = self._index_of(target)
        if index is not None and not _flag(request, _LIST_FLAG):
            body, content_type = self._reader.read(index)
            return Response.file(body, content_type)
        entries = [self._entry(child, relative) for child in _sorted(target)]
        heading = relative or self._heading
        return Response.html(
            listing.render(
                request.url,
                heading,
                entries,
                self._parent(relative),
                own_url=f"{_ANALYSES_PATH}{relative}",
                has_index=index is not None,
            )
        )

    def _entry(self, child: Path, relative: str) -> listing.Entry:
        info = child.stat()
        return listing.Entry(
            name=f"{child.name}/" if child.is_dir() else child.name,
            url=f"{_ANALYSES_PATH}{_joined(relative, child.name)}",
            size_bytes=None if child.is_dir() else info.st_size,
            changed_at=datetime.fromtimestamp(info.st_mtime, tz=UTC),
            raw_url=(
                f"{_ANALYSES_PATH}{_joined(relative, child.name)}?raw=1"
                if child.is_file() and media.is_readable_text(child)
                else ""
            ),
        )

    def _index_of(self, target: Path) -> Path | None:
        for name in _INDEX_NAMES:
            candidate = target / name
            if candidate.is_file():
                return candidate
        return None

    def _parent(self, relative: str) -> str | None:
        if not relative:
            return None
        parent = relative.rsplit("/", maxsplit=1)[0] if "/" in relative else ""
        return f"{_ANALYSES_PATH}{parent}"


def _sorted(target: Path) -> list[Path]:
    return sorted(target.iterdir(), key=lambda item: (item.is_file(), item.name.lower()))


def _joined(relative: str, name: str) -> str:
    return f"{relative}/{name}" if relative else name


def _wants_raw(request: Request) -> bool:
    return _flag(request, _RAW_FLAG)


def _flag(request: Request, name: str) -> bool:
    return request.query.get(name, "").lower() in _TRUTHY
