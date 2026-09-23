import re
from pathlib import Path

from rs_collector.dblogs.models import LogFile

_LOGS_DIR = "logs"
_NODE_DIR = "node_*"
_ROTATION = re.compile(r"^(?P<base>.+\.log)(?:\.(?P<index>\d+))?(?P<packed>\.gz)?$")
_SHARD_LOG = re.compile(r"^redis[-_]0*(?P<uid>\d+)(?:_info)?\.log")
_SYNC_LOG = re.compile(r"^(?:crdt_)?syncer[-_]0*(?P<uid>\d+)\.log")


class LogDiscovery:
    def __init__(self, root: Path) -> None:
        self._root = root

    def shard_logs(self, uid: str) -> tuple[LogFile, ...]:
        return self._matching(_SHARD_LOG, uid)

    def sync_logs(self, uid: str) -> tuple[LogFile, ...]:
        return self._matching(_SYNC_LOG, uid)

    def database_files(self, uid: str) -> tuple[Path, ...]:
        found = [path for path in sorted(self._root.rglob(f"database_{uid}*")) if path.is_file()]
        found.extend(
            path
            for pattern in (f"node_*/redis_{uid}.txt",)
            for path in sorted(self._root.rglob(pattern))
            if path.is_file()
        )
        return tuple(found)

    def shard_files(self, uid: str) -> tuple[Path, ...]:
        return tuple(
            path for path in sorted(self._root.rglob(f"node_*/redis_{uid}.txt")) if path.is_file()
        )

    def _matching(self, pattern: re.Pattern[str], uid: str) -> tuple[LogFile, ...]:
        found = [
            self._described(path) for path in self._log_files() if _belongs(pattern, path.name, uid)
        ]
        return tuple(sorted(found, key=lambda item: (item.node, -item.rotation)))

    def _log_files(self) -> tuple[Path, ...]:
        directories = [self._root, *self._root.glob(f"{_NODE_DIR}/{_LOGS_DIR}")]
        directories.extend(self._root.rglob(f"{_NODE_DIR}/{_LOGS_DIR}"))
        seen: dict[Path, None] = {}
        for directory in directories:
            if not directory.is_dir():
                continue
            for path in sorted(directory.iterdir()):
                if path.is_file():
                    seen.setdefault(path, None)
        return tuple(seen)

    def _described(self, path: Path) -> LogFile:
        match = _ROTATION.match(path.name)
        index = int(match.group("index")) if match and match.group("index") else 0
        return LogFile(
            path=path,
            node=_node_of(path, self._root),
            rotation=index,
            compressed=path.suffix == ".gz",
        )


def _belongs(pattern: re.Pattern[str], name: str, uid: str) -> bool:
    match = pattern.match(name)
    return match is not None and match.group("uid") == uid.lstrip("0")


def _node_of(path: Path, root: Path) -> str:
    for parent in path.parents:
        if parent.name.startswith("node_"):
            return parent.name
        if parent == root:
            break
    return ""
