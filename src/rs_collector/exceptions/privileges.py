from rs_collector.exceptions.base import RsCollectorError


class PrivilegeError(RsCollectorError):
    pass


class RunningAsRootError(PrivilegeError):
    pass
