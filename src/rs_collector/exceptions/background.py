from rs_collector.exceptions.base import RsCollectorError


class BackgroundError(RsCollectorError):
    pass


class ServerStartError(BackgroundError):
    pass


class ServerStopError(BackgroundError):
    pass


class CrontabError(BackgroundError):
    pass
