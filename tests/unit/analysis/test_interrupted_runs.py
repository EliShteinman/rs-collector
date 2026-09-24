import os
from datetime import UTC, datetime

import pytest

from rs_collector.analysis.models import AnalysisMetadata, AnalysisStatus
from rs_collector.analysis.options import AnalysisOptions
from rs_collector.analysis.repository import AnalysisRepository
from rs_collector.analysis.sweep import InterruptedRuns
from rs_collector.settings.models import AppSettings

pytestmark = pytest.mark.unit

_DEAD_PID = 2**22


@pytest.fixture
def repository(app_settings: AppSettings) -> AnalysisRepository:
    return AnalysisRepository(app_settings.storage)


def _stored(
    repository: AnalysisRepository,
    name: str,
    status: AnalysisStatus,
    runner_pid: int | None = None,
) -> None:
    repository.create(
        AnalysisMetadata(
            name=name,
            package_name="c1.example.com__2026-09-19_14-30-05",
            cluster_fqdn="c1.example.com",
            options=AnalysisOptions(),
            command=("redisscope", "--sp", "package.tar.gz"),
            analyzed_at=datetime(2026, 9, 19, 15, 0, 0, tzinfo=UTC),
            status=status,
            runner_pid=runner_pid,
        )
    )


def test_a_run_whose_process_is_gone_is_marked_interrupted(
    repository: AnalysisRepository,
) -> None:
    _stored(repository, "abandoned", AnalysisStatus.RUNNING, _DEAD_PID)

    InterruptedRuns(repository).mark()

    assert repository.get("abandoned").metadata.status is AnalysisStatus.INTERRUPTED


def test_the_abandoned_run_is_reported(repository: AnalysisRepository) -> None:
    _stored(repository, "abandoned", AnalysisStatus.RUNNING, _DEAD_PID)

    assert InterruptedRuns(repository).mark() == ("abandoned",)


def test_an_abandoned_run_gets_a_finishing_time(repository: AnalysisRepository) -> None:
    _stored(repository, "abandoned", AnalysisStatus.RUNNING, _DEAD_PID)

    InterruptedRuns(repository).mark()

    assert repository.get("abandoned").metadata.finished_at is not None


def test_a_run_of_this_process_is_left_alone(repository: AnalysisRepository) -> None:
    _stored(repository, "mine", AnalysisStatus.RUNNING, os.getpid())

    InterruptedRuns(repository).mark()

    assert repository.get("mine").metadata.status is AnalysisStatus.RUNNING


def test_a_run_without_a_process_is_taken_as_abandoned(repository: AnalysisRepository) -> None:
    _stored(repository, "from-an-older-release", AnalysisStatus.RUNNING)

    InterruptedRuns(repository).mark()

    assert repository.get("from-an-older-release").metadata.status is AnalysisStatus.INTERRUPTED


def test_a_finished_run_is_not_touched(repository: AnalysisRepository) -> None:
    _stored(repository, "done", AnalysisStatus.SUCCEEDED, _DEAD_PID)

    InterruptedRuns(repository).mark()

    assert repository.get("done").metadata.status is AnalysisStatus.SUCCEEDED


def test_nothing_to_sweep_reports_nothing(repository: AnalysisRepository) -> None:
    _stored(repository, "done", AnalysisStatus.SUCCEEDED)

    assert InterruptedRuns(repository).mark() == ()


def test_an_abandoned_run_gets_no_made_up_duration(repository: AnalysisRepository) -> None:
    _stored(repository, "abandoned", AnalysisStatus.RUNNING, _DEAD_PID)

    InterruptedRuns(repository).mark()

    assert repository.get("abandoned").metadata.duration_seconds is None
