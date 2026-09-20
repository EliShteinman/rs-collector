import fcntl
from pathlib import Path
from types import TracebackType
from typing import IO, Self

from rs_collector.exceptions.concurrency import CollectionAlreadyRunningError
from rs_collector.logging_setup.configurator import LoggerFactory

_LOCK_SUFFIX = ".lock"


class CollectionLock:
    def __init__(self, lock_path: Path) -> None:
        self._lock_path = lock_path
        self._file: IO[str] | None = None
        self._logger = LoggerFactory.for_component("concurrency")

    def __enter__(self) -> Self:
        self._lock_path.parent.mkdir(parents=True, exist_ok=True)
        handle = self._lock_path.open("w", encoding="utf-8")
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            handle.close()
            raise CollectionAlreadyRunningError(
                f"Another collection is already running for this cluster ({self._lock_path})"
            ) from error
        self._file = handle
        self._logger.debug("Took the lock %s", self._lock_path)
        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self._file is None:
            return
        fcntl.flock(self._file.fileno(), fcntl.LOCK_UN)
        self._file.close()
        self._file = None
        self._lock_path.unlink(missing_ok=True)
        self._logger.debug("Released the lock %s", self._lock_path)


class CollectionLockFactory:
    def __init__(self, locks_dir: Path) -> None:
        self._locks_dir = locks_dir

    def for_cluster(self, cluster_fqdn: str) -> CollectionLock:
        return CollectionLock(self._locks_dir / f"{cluster_fqdn}{_LOCK_SUFFIX}")
