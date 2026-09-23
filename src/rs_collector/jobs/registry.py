import threading
import uuid
from collections.abc import Callable

from rs_collector.exceptions.base import RsCollectorError
from rs_collector.exceptions.jobs import JobNotFoundError
from rs_collector.jobs.job import Job
from rs_collector.jobs.log_sink import JobLogCapture
from rs_collector.jobs.models import JobKind, JobView
from rs_collector.logging_setup.configurator import LoggerFactory

_IDENTIFIER_LENGTH = 12


class JobOutcome:
    def __init__(self, message: str, report_url: str = "") -> None:
        self.message = message
        self.report_url = report_url


class JobRegistry:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._order: list[str] = []
        self._lock = threading.Lock()
        self._logger = LoggerFactory.for_component("jobs")

    def start(self, kind: JobKind, title: str, work: Callable[[Job], JobOutcome]) -> Job:
        job = Job(uuid.uuid4().hex[:_IDENTIFIER_LENGTH], kind, title)
        with self._lock:
            self._jobs[job.id] = job
            self._order.append(job.id)
        threading.Thread(target=self._run, args=(job, work), daemon=True).start()
        self._logger.info("Started the %s job %s: %s", kind.value, job.id, title)
        return job

    def get(self, identifier: str) -> Job:
        with self._lock:
            job = self._jobs.get(identifier)
        if job is None:
            raise JobNotFoundError(f"No job named '{identifier}' is known")
        return job

    def list(self) -> tuple[JobView, ...]:
        with self._lock:
            jobs = [self._jobs[identifier] for identifier in reversed(self._order)]
        return tuple(job.view() for job in jobs)

    def _run(self, job: Job, work: Callable[[Job], JobOutcome]) -> None:
        with JobLogCapture(job):
            try:
                outcome = work(job)
            except RsCollectorError as error:
                job.write(f"Error: {error}")
                job.failed(str(error))
                self._logger.error("The job %s failed: %s", job.id, error)
                return
            job.succeeded(outcome.message, outcome.report_url)
            self._logger.info("The job %s finished", job.id)
