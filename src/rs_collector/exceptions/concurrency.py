from rs_collector.exceptions.base import RsCollectorError


class ConcurrencyError(RsCollectorError):
    pass


class CollectionAlreadyRunningError(ConcurrencyError):
    pass
