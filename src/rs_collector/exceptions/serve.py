from rs_collector.exceptions.base import RsCollectorError


class ServeError(RsCollectorError):
    pass


class DisplayServerStartError(ServeError):
    pass
