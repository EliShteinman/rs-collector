import json
from pathlib import Path
from typing import Any

from rs_collector.dblogs.models import Database, Shard
from rs_collector.logging_setup.configurator import LoggerFactory

_ENCODING = "utf-8"
_CCS_NAMES = ("ccs-redis.json", "ccs_redis.json")
_BDB_PREFIX = "bdb:"
_SHARD_LIST = "redis_list"
_NAME = "name"
_CRDT_KEYS = ("crdt", "crdt_sources", "crdt_guid", "crdt_replica_id")


class CcsDatabases:
    def __init__(self, root: Path) -> None:
        self._root = root
        self._logger = LoggerFactory.for_component("dblogs.ccs")

    def read(self) -> tuple[Database, ...]:
        for path in self._candidates():
            found = self._from_file(path)
            if found:
                self._logger.info("Read %d databases from %s", len(found), path)
                return found
        return ()

    def _candidates(self) -> tuple[Path, ...]:
        return tuple(
            path for name in _CCS_NAMES for path in sorted(self._root.rglob(name)) if path.is_file()
        )

    def _from_file(self, path: Path) -> tuple[Database, ...]:
        try:
            document = json.loads(path.read_text(encoding=_ENCODING, errors="replace"))
        except (OSError, json.JSONDecodeError) as error:
            self._logger.warning("%s cannot be read: %s", path, error)
            return ()
        return tuple(self._databases(document))

    def _databases(self, document: Any) -> list[Database]:
        if not isinstance(document, dict):
            return []
        found: list[Database] = []
        for key, value in document.items():
            if not str(key).startswith(_BDB_PREFIX) or not isinstance(value, dict):
                continue
            found.append(self._database(str(key).removeprefix(_BDB_PREFIX), value))
        return found

    def _database(self, uid: str, entry: dict[str, Any]) -> Database:
        return Database(
            uid=uid,
            name=str(entry.get(_NAME, "")),
            shards=tuple(Shard(uid=str(shard)) for shard in _shard_uids(entry)),
            active_active=any(_is_set(entry.get(key)) for key in _CRDT_KEYS),
        )


def _shard_uids(entry: dict[str, Any]) -> list[str]:
    raw = entry.get(_SHARD_LIST)
    if isinstance(raw, list):
        return [str(item) for item in raw]
    if isinstance(raw, str):
        return [part for part in raw.replace(",", " ").split() if part]
    return []


def _is_set(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() not in ("", "0", "false", "none", "null")
    if isinstance(value, (list, dict)):
        return bool(value)
    return value is not None and value != 0
