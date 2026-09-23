import logging
import threading
import time
from collections.abc import Iterator

import pytest

from rs_collector.exceptions.jobs import JobNotFoundError
from rs_collector.exceptions.storage import PackageNotFoundError
from rs_collector.jobs.job import Job
from rs_collector.jobs.models import JobKind, JobStatus
from rs_collector.jobs.registry import JobOutcome, JobRegistry
from rs_collector.logging_setup.configurator import LoggerFactory

pytestmark = pytest.mark.unit

_TIMEOUT_SECONDS = 5


def _wait_until_finished(registry: JobRegistry, identifier: str) -> None:
    deadline = time.monotonic() + _TIMEOUT_SECONDS
    while registry.get(identifier).view().is_running:
        assert time.monotonic() < deadline, "the job never finished"
        time.sleep(0.01)


@pytest.fixture(autouse=True)
def logging_level() -> Iterator[None]:
    logger = logging.getLogger("rs_collector")
    previous = logger.level
    logger.setLevel(logging.INFO)
    yield
    logger.setLevel(previous)


@pytest.fixture
def registry() -> JobRegistry:
    return JobRegistry()


def test_a_finished_job_reports_its_outcome(registry: JobRegistry) -> None:
    job = registry.start(JobKind.ANALYZE, "demo", lambda _: JobOutcome("all done"))

    _wait_until_finished(registry, job.id)

    assert registry.get(job.id).view().outcome == "all done"
    assert registry.get(job.id).view().status is JobStatus.SUCCEEDED


def test_console_output_of_the_job_is_kept(registry: JobRegistry) -> None:
    def work(job: Job) -> JobOutcome:
        job.write("step one")
        return JobOutcome("done")

    job = registry.start(JobKind.COLLECT, "demo", work)
    _wait_until_finished(registry, job.id)

    assert "step one" in registry.get(job.id).view().lines


def test_log_messages_of_the_job_are_kept(registry: JobRegistry) -> None:
    def work(_: Job) -> JobOutcome:
        LoggerFactory.for_component("test").info("connecting to the cluster")
        return JobOutcome("done")

    job = registry.start(JobKind.COLLECT, "demo", work)
    _wait_until_finished(registry, job.id)

    assert any("connecting to the cluster" in line for line in registry.get(job.id).view().lines)


def test_a_failing_job_keeps_the_error(registry: JobRegistry) -> None:
    def work(_: Job) -> JobOutcome:
        raise PackageNotFoundError("no package is stored")

    job = registry.start(JobKind.ANALYZE, "demo", work)
    _wait_until_finished(registry, job.id)

    view = registry.get(job.id).view()
    assert view.status is JobStatus.FAILED
    assert view.outcome == "no package is stored"


def test_two_jobs_do_not_mix_their_logs(registry: JobRegistry) -> None:
    started = threading.Event()

    def slow(_: Job) -> JobOutcome:
        LoggerFactory.for_component("test").info("slow job speaking")
        started.set()
        time.sleep(0.2)
        return JobOutcome("done")

    def quick(_: Job) -> JobOutcome:
        assert started.wait(_TIMEOUT_SECONDS)
        LoggerFactory.for_component("test").info("quick job speaking")
        return JobOutcome("done")

    slow_job = registry.start(JobKind.COLLECT, "slow", slow)
    quick_job = registry.start(JobKind.ANALYZE, "quick", quick)
    _wait_until_finished(registry, slow_job.id)
    _wait_until_finished(registry, quick_job.id)

    quick_lines = "\n".join(registry.get(quick_job.id).view().lines)
    assert "quick job speaking" in quick_lines
    assert "slow job speaking" not in quick_lines


def test_only_new_lines_are_returned(registry: JobRegistry) -> None:
    def work(job: Job) -> JobOutcome:
        job.write("first")
        job.write("second")
        return JobOutcome("done")

    job = registry.start(JobKind.COLLECT, "demo", work)
    _wait_until_finished(registry, job.id)

    assert registry.get(job.id).view(from_line=1).lines[0] == "second"


def test_an_unknown_job_is_reported(registry: JobRegistry) -> None:
    with pytest.raises(JobNotFoundError):
        registry.get("missing")


def test_the_newest_job_is_listed_first(registry: JobRegistry) -> None:
    first = registry.start(JobKind.COLLECT, "first", lambda _: JobOutcome("done"))
    second = registry.start(JobKind.ANALYZE, "second", lambda _: JobOutcome("done"))
    _wait_until_finished(registry, first.id)
    _wait_until_finished(registry, second.id)

    assert [view.title for view in registry.list()] == ["second", "first"]


def test_only_the_newest_runs_are_remembered() -> None:
    registry = JobRegistry(max_jobs=2, max_lines=10)
    for number in range(3):
        started = registry.start(JobKind.ANALYZE, f"run {number}", lambda _: JobOutcome("done"))
        _wait_until_finished(registry, started.id)

    assert [view.title for view in registry.list()] == ["run 2", "run 1"]


def test_a_talkative_job_keeps_its_last_lines() -> None:
    registry = JobRegistry(max_jobs=10, max_lines=5)

    def work(job: Job) -> JobOutcome:
        for number in range(20):
            job.write(f"line {number}")
        return JobOutcome("done")

    job = registry.start(JobKind.ANALYZE, "talkative", work)
    _wait_until_finished(registry, job.id)

    view = registry.get(job.id).view()
    assert len(view.lines) == 5
    assert "line 19" in view.lines


def test_the_reader_is_told_where_to_continue() -> None:
    registry = JobRegistry(max_jobs=10, max_lines=100)

    def work(job: Job) -> JobOutcome:
        job.write("first")
        job.write("second")
        return JobOutcome("done")

    job = registry.start(JobKind.COLLECT, "demo", work)
    _wait_until_finished(registry, job.id)

    everything = registry.get(job.id).view()
    later = registry.get(job.id).view(from_line=1)
    assert later.lines == everything.lines[1:]
    assert later.next_line == everything.next_line == len(everything.lines)


def test_a_job_that_crashes_is_marked_failed(registry: JobRegistry) -> None:
    def work(_: Job) -> JobOutcome:
        raise TypeError("nobody expected this")

    job = registry.start(JobKind.ANALYZE, "demo", work)
    _wait_until_finished(registry, job.id)

    view = registry.get(job.id).view()
    assert view.status is JobStatus.FAILED
    assert "nobody expected this" in view.outcome
