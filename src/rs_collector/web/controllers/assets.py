from collections.abc import Mapping

from rs_collector.web import assets
from rs_collector.web.http import Request, Response

_CSS = "text/css; charset=utf-8"
_JAVASCRIPT = "text/javascript; charset=utf-8"
_ENCODING = "utf-8"


class AssetsController:
    def stylesheet(self, _: Request, __: Mapping[str, str]) -> Response:
        return Response.file(assets.CSS.encode(_ENCODING), _CSS)

    def javascript(self, _: Request, __: Mapping[str, str]) -> Response:
        return Response.file(assets.JAVASCRIPT.encode(_ENCODING), _JAVASCRIPT)
