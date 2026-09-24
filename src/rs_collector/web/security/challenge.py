from rs_collector.web.http import Request, Response
from rs_collector.web.views import locked

_UNAUTHORIZED_STATUS = 401
_CHALLENGE_HEADER = "WWW-Authenticate"


def challenge(request: Request, realm: str) -> Response:
    return Response.html(
        locked.render(request.url),
        status=_UNAUTHORIZED_STATUS,
        headers={_CHALLENGE_HEADER: f'Basic realm="{realm}", charset="UTF-8"'},
    )
