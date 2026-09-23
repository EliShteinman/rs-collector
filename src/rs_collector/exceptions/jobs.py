from rs_collector.exceptions.base import RsCollectorError


class JobError(RsCollectorError):
    pass


class JobNotFoundError(JobError):
    pass
