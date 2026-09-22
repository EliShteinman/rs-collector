import fcntl
from contextlib import ExitStack
from pathlib import Path

import pytest

from rs_collector.concurrency.lock import CollectionLockFactory
from rs_collector.exceptions.concurrency import CollectionAlreadyRunningError

pytestmark = pytest.mark.unit


@pytest.fixture
def locks(tmp_path: Path) -> CollectionLockFactory:
    return CollectionLockFactory(tmp_path / "locks")


def test_a_lock_can_be_taken(locks: CollectionLockFactory, tmp_path: Path) -> None:
    with locks.for_cluster("c1.example.com"):
        assert (tmp_path / "locks" / "c1.example.com.lock").is_file()


def test_a_second_collection_of_the_same_cluster_is_refused(
    locks: CollectionLockFactory,
) -> None:
    with (
        locks.for_cluster("c1.example.com"),
        pytest.raises(CollectionAlreadyRunningError),
        locks.for_cluster("c1.example.com"),
    ):
        pass


def test_another_cluster_can_be_collected_at_the_same_time(
    locks: CollectionLockFactory,
) -> None:
    with locks.for_cluster("c1.example.com"), locks.for_cluster("c2.example.com"):
        assert True


def test_the_lock_is_released_after_use(locks: CollectionLockFactory) -> None:
    with locks.for_cluster("c1.example.com"):
        pass

    with locks.for_cluster("c1.example.com"):
        assert True


def test_the_lock_is_released_after_a_failure(locks: CollectionLockFactory) -> None:
    with pytest.raises(ValueError, match="boom"), locks.for_cluster("c1.example.com"):
        raise ValueError("boom")

    with locks.for_cluster("c1.example.com"):
        assert True


def test_a_waiting_collection_cannot_slip_past_a_released_lock(
    locks: CollectionLockFactory, tmp_path: Path
) -> None:
    with ExitStack() as stack:
        with locks.for_cluster("c1.example.com"):
            waiter = stack.enter_context((tmp_path / "locks" / "c1.example.com.lock").open())
        fcntl.flock(waiter.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

        with pytest.raises(CollectionAlreadyRunningError), locks.for_cluster("c1.example.com"):
            pass
