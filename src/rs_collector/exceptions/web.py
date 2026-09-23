from rs_collector.exceptions.base import RsCollectorError


class WebError(RsCollectorError):
    pass


class RouteNotFoundError(WebError):
    pass


class BadRequestError(WebError):
    pass
