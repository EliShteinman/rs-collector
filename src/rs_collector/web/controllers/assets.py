from collections.abc import Mapping
from importlib import resources

from rs_collector.exceptions.storage import ArtifactNotFoundError
from rs_collector.web import assets
from rs_collector.web.http import Request, Response

_CSS = "text/css; charset=utf-8"
_JAVASCRIPT = "text/javascript; charset=utf-8"
_FONT = "font/woff2"
_FONT_PACKAGE = "rs_collector.web.fonts"
_FONTS = ("plex-sans.woff2", "plex-mono.woff2")
_ENCODING = "utf-8"
_IMMUTABLE = {"Cache-Control": "public, max-age=604800, immutable"}


class AssetsController:
    def stylesheet(self, _: Request, __: Mapping[str, str]) -> Response:
        return Response.file(assets.CSS.encode(_ENCODING), _CSS)

    def javascript(self, _: Request, __: Mapping[str, str]) -> Response:
        return Response.file(assets.JAVASCRIPT.encode(_ENCODING), _JAVASCRIPT)

    def font(self, _: Request, parameters: Mapping[str, str]) -> Response:
        name = parameters["name"]
        if name not in _FONTS:
            raise ArtifactNotFoundError(f"No font named '{name}' is bundled")
        content = resources.files(_FONT_PACKAGE).joinpath(name).read_bytes()
        return Response(body=content, content_type=_FONT, headers=_IMMUTABLE)
