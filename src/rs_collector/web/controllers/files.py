import mimetypes
from collections.abc import Mapping
from pathlib import Path

from rs_collector.exceptions.storage import ArtifactNotFoundError
from rs_collector.logging_setup.configurator import LoggerFactory
from rs_collector.web.http import Request, Response
from rs_collector.web.views import listing

_DEFAULT_TYPE = "application/octet-stream"
_ANALYSES_PATH = "/analyses/"
_INDEX_FILES = ("index.html",)


class FilesController:
    def __init__(self, root: Path, heading: str = "Analyses") -> None:
        self._root = root
        self._heading = heading
        self._logger = LoggerFactory.for_component("web.files")

    def serve(self, request: Request, parameters: Mapping[str, str]) -> Response:
        relative = parameters.get("path", "").strip("/")
        target = self._resolved(relative)
        if target.is_dir():
            return self._directory(request, target, relative)
        if target.is_file():
            return Response.file(target.read_bytes(), _content_type(target))
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
        if index is not None:
            return Response.file(index.read_bytes(), _content_type(index))
        entries = [
            listing.Entry(
                name=f"{child.name}/" if child.is_dir() else child.name,
                url=f"{_ANALYSES_PATH}{_joined(relative, child.name)}",
            )
            for child in sorted(target.iterdir(), key=lambda item: (item.is_file(), item.name))
        ]
        heading = relative or self._heading
        return Response.html(listing.render(request.url, heading, entries, self._parent(relative)))

    def _index_of(self, target: Path) -> Path | None:
        for name in _INDEX_FILES:
            candidate = target / name
            if candidate.is_file():
                return candidate
        return None

    def _parent(self, relative: str) -> str | None:
        if not relative:
            return None
        parent = relative.rsplit("/", maxsplit=1)[0] if "/" in relative else ""
        return f"{_ANALYSES_PATH}{parent}"


def _joined(relative: str, name: str) -> str:
    return f"{relative}/{name}" if relative else name


def _content_type(target: Path) -> str:
    guessed, _ = mimetypes.guess_type(target.name)
    return guessed or _DEFAULT_TYPE
