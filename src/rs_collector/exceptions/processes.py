from rs_collector.exceptions.base import RsCollectorError


class ProcessError(RsCollectorError):
    pass


class ProcessTimeoutError(ProcessError):
    pass


class ProcessStartError(ProcessError):
    pass
