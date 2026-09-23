from pathlib import Path

import pytest

from rs_collector.dblogs.inventory import PackageInventory
from rs_collector.dblogs.rladmin import RladminTopology

pytestmark = pytest.mark.unit


def test_the_databases_of_the_package_are_listed(support_package: Path) -> None:
    databases = PackageInventory(support_package).databases()

    assert [(database.uid, database.name) for database in databases] == [
        ("1", "orders"),
        ("2", "sessions"),
    ]


def test_the_shards_of_a_database_are_known(support_package: Path) -> None:
    orders = PackageInventory(support_package).find("orders")

    assert orders is not None
    assert [shard.uid for shard in orders.shards] == ["3", "4"]


def test_the_node_and_role_of_each_shard_come_from_rladmin(support_package: Path) -> None:
    orders = PackageInventory(support_package).find("1")

    assert orders is not None
    assert [(shard.uid, shard.node, shard.role) for shard in orders.shards] == [
        ("3", "1", "master"),
        ("4", "2", "slave"),
    ]


def test_an_active_active_database_is_recognized(support_package: Path) -> None:
    sessions = PackageInventory(support_package).find("sessions")

    assert sessions is not None and sessions.active_active


def test_a_plain_database_is_not_marked_active_active(support_package: Path) -> None:
    orders = PackageInventory(support_package).find("orders")

    assert orders is not None and not orders.active_active


def test_a_database_can_be_found_by_its_number(support_package: Path) -> None:
    assert PackageInventory(support_package).find("2") is not None


def test_an_unknown_database_is_not_found(support_package: Path) -> None:
    assert PackageInventory(support_package).find("nothing") is None


def test_rladmin_alone_is_enough(support_package: Path) -> None:
    (support_package / "node_1" / "ccs_redis.json").unlink()

    databases = PackageInventory(support_package).databases()

    assert [(database.uid, database.name) for database in databases] == [
        ("1", "orders"),
        ("2", "sessions"),
    ]


def test_the_rladmin_reader_skips_everything_that_is_not_a_shard_line(
    support_package: Path,
) -> None:
    databases = RladminTopology(support_package).read()

    assert sum(len(database.shards) for database in databases) == 3
