import re
from pathlib import Path

from rs_collector.dblogs.models import Database, Shard
from rs_collector.logging_setup.configurator import LoggerFactory

_ENCODING = "utf-8"
_DIRECTORY = "database_*"
_UID = re.compile(r"^database_(?P<uid>\d+)$")
_CCS_INFO = "database_{uid}_ccs_info.txt"
_SHARD_LIST = re.compile(r"redis_list[^0-9\[]*\[?(?P<uids>[0-9,\s'\"]+)")
_NAME = re.compile(r"[\"']?name[\"']?\s*[:=]\s*[\"']?(?P<name>[A-Za-z0-9_.-]+)")
_CRDT = re.compile(r"crdt(?:_guid|_sources|_replica_id)?\s*[:=]\s*[\"']?(?P<value>[^,\s\"'}]+)")
_FALSE = ("false", "none", "null", "0", "")


class DatabaseDirectories:
    def __init__(self, root: Path) -> None:
        self._root = root
        self._logger = LoggerFactory.for_component("dblogs.database_dirs")

    def read(self) -> tuple[Database, ...]:
        return tuple(
            self._database(directory) for directory in sorted(self._directories(), key=_number)
        )

    def directory_of(self, uid: str) -> Path | None:
        for directory in self._directories():
            match = _UID.match(directory.name)
            if match is not None and match.group("uid") == uid:
                return directory
        return None

    def _directories(self) -> tuple[Path, ...]:
        return tuple(
            path
            for path in sorted(self._root.rglob(_DIRECTORY))
            if path.is_dir() and _UID.match(path.name)
        )

    def _database(self, directory: Path) -> Database:
        uid = str(_UID.match(directory.name).group("uid"))  # type: ignore[union-attr]
        text = self._ccs_info(directory, uid)
        return Database(
            uid=uid,
            name=self._name(text),
            shards=tuple(Shard(uid=shard) for shard in _shard_uids(text)),
            active_active=_is_active_active(text),
        )

    def _ccs_info(self, directory: Path, uid: str) -> str:
        path = directory / _CCS_INFO.format(uid=uid)
        try:
            return path.read_text(encoding=_ENCODING, errors="replace")
        except OSError:
            self._logger.debug("No CCS info for database %s", uid)
            return ""

    def _name(self, text: str) -> str:
        match = _NAME.search(text)
        return match.group("name") if match is not None else ""


def _number(directory: Path) -> int:
    match = _UID.match(directory.name)
    return int(match.group("uid")) if match is not None else 0


def _shard_uids(text: str) -> list[str]:
    match = _SHARD_LIST.search(text)
    if match is None:
        return []
    return [part for part in re.split(r"[,\s'\"]+", match.group("uids")) if part.isdigit()]


def _is_active_active(text: str) -> bool:
    return any(match.group("value").strip().lower() not in _FALSE for match in _CRDT.finditer(text))
