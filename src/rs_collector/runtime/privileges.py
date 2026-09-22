import os
from collections.abc import Callable

from rs_collector.exceptions.privileges import RunningAsRootError
from rs_collector.logging_setup.configurator import LoggerFactory

_ROOT_USER_ID = 0


class PrivilegeGuard:
    def __init__(self, effective_user_id: Callable[[], int] = os.geteuid) -> None:
        self._effective_user_id = effective_user_id
        self._logger = LoggerFactory.for_component("runtime.privileges")

    def refuse_root(self) -> None:
        if self._effective_user_id() != _ROOT_USER_ID:
            return
        self._logger.error("rsc was started as root")
        raise RunningAsRootError(
            "rsc runs as a regular user. Root is only used on the cluster nodes, through sudo."
        )
