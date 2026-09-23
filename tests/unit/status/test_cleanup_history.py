from datetime import UTC, datetime

import pytest

from rs_collector.retention.cleaner import CleanupReport
from rs_collector.retention.history import CleanupHistory
from rs_collector.settings.models import AppSettings

pytestmark = pytest.mark.unit


@pytest.fixture
def history(app_settings: AppSettings) -> CleanupHistory:
    return CleanupHistory(app_settings.storage)


def test_nothing_is_recorded_before_the_first_cleanup(history: CleanupHistory) -> None:
    assert history.last() is None


def test_a_cleanup_is_recorded_with_its_counts(history: CleanupHistory) -> None:
    history.record(CleanupReport(removed_packages=("a", "b"), removed_analyses=("c",)))

    last = history.last()
    assert last is not None
    assert (last.removed_packages, last.removed_analyses) == (2, 1)


def test_the_recorded_time_is_kept(history: CleanupHistory) -> None:
    moment = datetime(2026, 9, 23, 3, 30, tzinfo=UTC)

    history.record(CleanupReport(), finished_at=moment)

    last = history.last()
    assert last is not None and last.finished_at == moment


def test_a_broken_record_is_ignored(history: CleanupHistory, app_settings: AppSettings) -> None:
    path = app_settings.storage.cleanup_history_file
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{not json", encoding="utf-8")

    assert history.last() is None
