from pathlib import Path

from rs_collector.dblogs.ccs import CcsDatabases
from rs_collector.dblogs.database_dirs import DatabaseDirectories
from rs_collector.dblogs.models import Database, Shard
from rs_collector.dblogs.rladmin import RladminTopology
from rs_collector.logging_setup.configurator import LoggerFactory


class PackageInventory:
    def __init__(self, root: Path) -> None:
        self._root = root
        self._logger = LoggerFactory.for_component("dblogs.inventory")

    def databases(self) -> tuple[Database, ...]:
        from_rladmin = RladminTopology(self._root).read()
        known = CcsDatabases(self._root).read() or DatabaseDirectories(self._root).read()
        if not known:
            self._logger.info("Using the rladmin output for the database topology")
            return from_rladmin
        return tuple(self._enriched(database, from_rladmin) for database in known)

    def _enriched(self, database: Database, others: tuple[Database, ...]) -> Database:
        known = {
            shard.uid: shard
            for other in others
            if other.uid == database.uid
            for shard in other.shards
        }
        shards = database.shards or tuple(known.values())
        return database.model_copy(
            update={
                "shards": tuple(known.get(shard.uid, shard) for shard in shards),
                "name": database.name
                or next((other.name for other in others if other.uid == database.uid), ""),
            }
        )

    def find(self, asked: str) -> Database | None:
        for database in self.databases():
            if database.answers_to(asked):
                return database
        return None

    def with_shards(self, asked: str, shards: tuple[str, ...]) -> Database:
        return Database(uid=asked, shards=tuple(Shard(uid=uid) for uid in shards))
