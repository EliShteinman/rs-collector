from rs_collector.exceptions.base import RsCollectorError


class SelectionError(RsCollectorError):
    pass


class ConnectionStringError(SelectionError):
    pass


class ClusterNotFoundError(SelectionError):
    pass


class EmptyInventoryError(SelectionError):
    pass


class SelectionAbortedError(SelectionError):
    pass
