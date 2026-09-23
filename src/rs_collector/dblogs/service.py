from pathlib import Path

from rs_collector.dblogs.discovery import LogDiscovery
from rs_collector.dblogs.inventory import PackageInventory
from rs_collector.dblogs.merge import LogMerger
from rs_collector.dblogs.models import Database, DatabaseLogs, MergedLog, PackageFile, Shard
from rs_collector.exceptions.dblogs import DatabaseNotFoundError, NoLogsForDatabaseError
from rs_collector.logging_setup.configurator import LoggerFactory

_SHARD_TITLE = "shard {uid}"
_SYNC_TITLE = "sync of database {uid}"
_SHARD_FILE = "shard-{uid}.log"
_SYNC_FILE = "sync-{uid}.log"


class DatabaseLogService:
    def __init__(self, package_root: Path, output_root: Path) -> None:
        self._package_root = package_root
        self._output_root = output_root
        self._inventory = PackageInventory(package_root)
        self._discovery = LogDiscovery(package_root)
        self._merger = LogMerger()
        self._logger = LoggerFactory.for_component("dblogs")

    def databases(self) -> tuple[Database, ...]:
        return self._inventory.databases()

    def collect(self, asked: str) -> DatabaseLogs:
        database = self._inventory.find(asked)
        if database is None:
            raise DatabaseNotFoundError(
                f"No database named or numbered '{asked}' is in this support package"
            )
        logs = DatabaseLogs(
            database=database,
            shard_logs=self._shard_logs(database),
            sync_logs=self._sync_logs(database),
            package_files=self._package_files(database),
        )
        if not logs.merged:
            raise NoLogsForDatabaseError(
                f"The support package holds no log file of database '{asked}'"
            )
        self._logger.info("Collected %d merged logs for %s", len(logs.merged), database.uid)
        return logs

    def _shard_logs(self, database: Database) -> tuple[MergedLog, ...]:
        return tuple(
            merged
            for shard in database.shards
            if (merged := self._shard_log(database, shard)) is not None
        )

    def _shard_log(self, database: Database, shard: Shard) -> MergedLog | None:
        sources = self._discovery.shard_logs(shard.uid)
        if not sources:
            return None
        return self._merger.merge(
            _SHARD_TITLE.format(uid=shard.uid),
            sources,
            self._directory(database) / _SHARD_FILE.format(uid=shard.uid),
            node=shard.node,
            role=shard.role,
        )

    def _sync_logs(self, database: Database) -> tuple[MergedLog, ...]:
        sources = self._discovery.sync_logs(database.uid)
        if not sources:
            return ()
        return (
            self._merger.merge(
                _SYNC_TITLE.format(uid=database.uid),
                sources,
                self._directory(database) / _SYNC_FILE.format(uid=database.uid),
            ),
        )

    def _package_files(self, database: Database) -> tuple[PackageFile, ...]:
        found = list(self._discovery.database_files(database.uid))
        for shard in database.shards:
            found.extend(self._discovery.shard_files(shard.uid))
        return tuple(
            PackageFile(path=path, byte_count=path.stat().st_size) for path in dict.fromkeys(found)
        )

    def _directory(self, database: Database) -> Path:
        return self._output_root / database.uid
