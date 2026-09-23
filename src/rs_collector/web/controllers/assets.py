from collections.abc import Mapping
from pathlib import Path

from rs_collector.exceptions.storage import ArtifactNotFoundError
from rs_collector.runtime.bundle import BundleLocator
from rs_collector.web import assets
from rs_collector.web.http import Request, Response

_CSS = "text/css; charset=utf-8"
_JAVASCRIPT = "text/javascript; charset=utf-8"
_FONT = "font/woff2"
_FONTS = ("plex-sans.woff2", "plex-mono.woff2")
_FONT_DIRECTORY = ("web", "fonts")
_ENCODING = "utf-8"
_IMMUTABLE = {"Cache-Control": "public, max-age=604800, immutable"}


class AssetsController:
    def __init__(self, fonts: Path | None = None) -> None:
        self._fonts = fonts or BundleLocator().bundled(*_FONT_DIRECTORY)

    def stylesheet(self, _: Request, __: Mapping[str, str]) -> Response:
        return Response.file(assets.CSS.encode(_ENCODING), _CSS)

    def javascript(self, _: Request, __: Mapping[str, str]) -> Response:
        return Response.file(assets.JAVASCRIPT.encode(_ENCODING), _JAVASCRIPT)

    def font(self, _: Request, parameters: Mapping[str, str]) -> Response:
        name = parameters["name"]
        path = self._fonts / name
        if name not in _FONTS or not path.is_file():
            raise ArtifactNotFoundError(f"No font named '{name}' is bundled")
        return Response(body=path.read_bytes(), content_type=_FONT, headers=_IMMUTABLE)
