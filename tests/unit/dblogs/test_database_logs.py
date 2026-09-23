import gzip
from pathlib import Path

import pytest

from rs_collector.dblogs.service import DatabaseLogService
from rs_collector.exceptions.dblogs import DatabaseNotFoundError, NoLogsForDatabaseError

pytestmark = pytest.mark.unit


@pytest.fixture
def service(support_package: Path, tmp_path: Path) -> DatabaseLogService:
    return DatabaseLogService(support_package, tmp_path / "db-logs")


def test_every_shard_of_the_database_gets_one_merged_log(
    service: DatabaseLogService,
) -> None:
    logs = service.collect("orders")

    assert [log.title for log in logs.shard_logs] == ["shard 3", "shard 4"]


def test_the_rotation_of_a_shard_is_merged_oldest_first(service: DatabaseLogService) -> None:
    logs = service.collect("orders")

    text = logs.shard_logs[0].path.read_text(encoding="utf-8")
    assert text.index("oldest line") < text.index("older line") < text.index("newest line")


def test_a_compressed_rotation_is_unpacked_into_the_merged_log(
    service: DatabaseLogService,
) -> None:
    logs = service.collect("orders")

    assert "oldest line of shard 3" in logs.shard_logs[0].path.read_text(encoding="utf-8")


def test_the_merged_log_knows_its_node_and_role(service: DatabaseLogService) -> None:
    logs = service.collect("orders")

    assert (logs.shard_logs[0].node, logs.shard_logs[0].role) == ("1", "master")


def test_the_merged_log_reports_the_time_it_covers(service: DatabaseLogService) -> None:
    logs = service.collect("orders")

    first = logs.shard_logs[0]
    assert first.first_seen is not None and first.last_seen is not None
    assert first.first_seen < first.last_seen


def test_each_source_file_is_recorded(service: DatabaseLogService) -> None:
    logs = service.collect("orders")

    assert [path.name for path in logs.shard_logs[0].sources] == [
        "redis_3.log.2.gz",
        "redis_3.log.1",
        "redis_3.log",
    ]


def test_the_sync_log_of_an_active_active_database_is_included(
    service: DatabaseLogService,
) -> None:
    logs = service.collect("sessions")

    assert [log.title for log in logs.sync_logs] == ["sync of database 2"]
    assert "syncing from the remote cluster" in logs.sync_logs[0].path.read_text(encoding="utf-8")


def test_a_plain_database_has_no_sync_log(service: DatabaseLogService) -> None:
    assert service.collect("orders").sync_logs == ()


def test_logs_of_other_shards_are_not_included(service: DatabaseLogService) -> None:
    logs = service.collect("orders")

    merged = "\n".join(log.path.read_text(encoding="utf-8") for log in logs.merged)
    assert "line of shard 7" not in merged
    assert "not a shard log" not in merged


def test_an_unknown_database_is_reported(service: DatabaseLogService) -> None:
    with pytest.raises(DatabaseNotFoundError):
        service.collect("nothing")


def test_a_database_without_logs_is_reported(support_package: Path, tmp_path: Path) -> None:
    for path in support_package.rglob("redis_7.log"):
        path.unlink()
    for path in support_package.rglob("crdt_syncer-2.log"):
        path.unlink()

    with pytest.raises(NoLogsForDatabaseError):
        DatabaseLogService(support_package, tmp_path / "out").collect("sessions")


def test_a_broken_archive_does_not_stop_the_merge(support_package: Path, tmp_path: Path) -> None:
    (support_package / "node_1" / "logs" / "redis_3.log.3.gz").write_bytes(b"not gzip")

    logs = DatabaseLogService(support_package, tmp_path / "out").collect("orders")

    text = logs.shard_logs[0].path.read_text(encoding="utf-8")
    assert "could not be read" in text
    assert "newest line of shard 3" in text


def test_the_merged_log_counts_its_lines(service: DatabaseLogService) -> None:
    logs = service.collect("orders")

    assert logs.shard_logs[0].lines == 3


def test_a_gzip_only_rotation_still_merges(support_package: Path, tmp_path: Path) -> None:
    logs_dir = support_package / "node_2" / "logs"
    (logs_dir / "redis_4.log").unlink()
    (logs_dir / "redis_4.log.1.gz").write_bytes(gzip.compress(b"only the archive remains\n"))

    logs = DatabaseLogService(support_package, tmp_path / "out").collect("orders")

    assert "only the archive remains" in logs.shard_logs[1].path.read_text(encoding="utf-8")


def test_the_files_the_package_holds_for_the_database_are_listed(
    service: DatabaseLogService,
) -> None:
    logs = service.collect("orders")

    assert [file.path.name for file in logs.package_files] == []


def test_the_database_directory_files_are_listed_when_present(
    support_package: Path, tmp_path: Path
) -> None:
    directory = support_package / "database_1"
    directory.mkdir()
    (directory / "database_1.slowlog").write_text("slow command\n", encoding="utf-8")
    (directory / "database_1.info").write_text("used_memory:1\n", encoding="utf-8")
    (support_package / "node_1" / "redis_3.txt").write_text("shard info\n", encoding="utf-8")

    logs = DatabaseLogService(support_package, tmp_path / "out").collect("orders")

    assert [file.path.name for file in logs.package_files] == [
        "database_1.info",
        "database_1.slowlog",
        "redis_3.txt",
    ]
