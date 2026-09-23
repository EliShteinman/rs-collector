from pathlib import Path

import pytest

from rs_collector.dblogs.database_dirs import DatabaseDirectories
from rs_collector.dblogs.inventory import PackageInventory

pytestmark = pytest.mark.unit

_CCS_INFO_ONE = """bdb:5
name: payments
redis_list: [11, 12]
crdt: False
replication: enabled
"""

_CCS_INFO_TWO = """bdb:6
name: catalog
redis_list: [13]
crdt: True
crdt_guid: 9f1c
"""


@pytest.fixture
def package_with_database_dirs(tmp_path: Path) -> Path:
    root = tmp_path / "redisscope_sp"
    for uid, text in (("5", _CCS_INFO_ONE), ("6", _CCS_INFO_TWO)):
        directory = root / f"database_{uid}"
        directory.mkdir(parents=True)
        (directory / f"database_{uid}_ccs_info.txt").write_text(text, encoding="utf-8")
        (directory / f"database_{uid}.slowlog").write_text("slow command\n", encoding="utf-8")
    (root / "node_1" / "logs").mkdir(parents=True)
    (root / "node_1" / "logs" / "redis_11.log").write_text(
        "11:M 23 Sep 2026 10:00:00.100 * shard 11 line\n", encoding="utf-8"
    )
    return root


def test_the_database_directories_are_read(package_with_database_dirs: Path) -> None:
    databases = DatabaseDirectories(package_with_database_dirs).read()

    assert [(database.uid, database.name) for database in databases] == [
        ("5", "payments"),
        ("6", "catalog"),
    ]


def test_the_shards_come_from_the_ccs_info_file(package_with_database_dirs: Path) -> None:
    payments = DatabaseDirectories(package_with_database_dirs).read()[0]

    assert [shard.uid for shard in payments.shards] == ["11", "12"]


def test_an_active_active_database_is_recognized(package_with_database_dirs: Path) -> None:
    catalog = DatabaseDirectories(package_with_database_dirs).read()[1]

    assert catalog.active_active


def test_a_plain_database_is_not_marked(package_with_database_dirs: Path) -> None:
    assert not DatabaseDirectories(package_with_database_dirs).read()[0].active_active


def test_the_inventory_uses_the_database_directories_when_there_is_no_ccs(
    package_with_database_dirs: Path,
) -> None:
    found = PackageInventory(package_with_database_dirs).find("payments")

    assert found is not None and [shard.uid for shard in found.shards] == ["11", "12"]


def test_the_directory_of_a_database_is_found(package_with_database_dirs: Path) -> None:
    directory = DatabaseDirectories(package_with_database_dirs).directory_of("6")

    assert directory is not None and directory.name == "database_6"
