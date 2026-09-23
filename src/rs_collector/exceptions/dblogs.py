from rs_collector.exceptions.base import RsCollectorError


class DatabaseLogsError(RsCollectorError):
    pass


class DatabaseNotFoundError(DatabaseLogsError):
    pass


class NoLogsForDatabaseError(DatabaseLogsError):
    pass
