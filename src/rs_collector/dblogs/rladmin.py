import re
from pathlib import Path

from rs_collector.dblogs.models import Database, Shard
from rs_collector.logging_setup.configurator import LoggerFactory

_ENCODING = "utf-8"
_RLADMIN_NAMES = ("*.rladmin", "rladmin_status.log", "rladmin.log")
_SHARD_LINE = re.compile(
    r"^db:(?P<db>\d+)\s+(?P<name>\S+)\s+redis:(?P<shard>\d+)\s+node:(?P<node>\d+)\s+(?P<role>\S+)"
)


class RladminTopology:
    def __init__(self, root: Path) -> None:
        self._root = root
        self._logger = LoggerFactory.for_component("dblogs.rladmin")

    def read(self) -> tuple[Database, ...]:
        shards: dict[str, dict[str, Shard]] = {}
        names: dict[str, str] = {}
        for path in self._candidates():
            self._collect(path, shards, names)
        return tuple(
            Database(uid=uid, name=names.get(uid, ""), shards=tuple(found.values()))
            for uid, found in sorted(shards.items(), key=lambda item: int(item[0]))
        )

    def _candidates(self) -> tuple[Path, ...]:
        return tuple(
            path
            for pattern in _RLADMIN_NAMES
            for path in sorted(self._root.rglob(pattern))
            if path.is_file()
        )

    def _collect(
        self, path: Path, shards: dict[str, dict[str, Shard]], names: dict[str, str]
    ) -> None:
        try:
            text = path.read_text(encoding=_ENCODING, errors="replace")
        except OSError as error:
            self._logger.warning("%s cannot be read: %s", path, error)
            return
        for line in text.splitlines():
            match = _SHARD_LINE.match(line.strip())
            if match is None:
                continue
            database = match.group("db")
            names.setdefault(database, match.group("name"))
            shards.setdefault(database, {})[match.group("shard")] = Shard(
                uid=match.group("shard"), node=match.group("node"), role=match.group("role")
            )
