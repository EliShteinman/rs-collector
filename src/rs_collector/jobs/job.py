import threading
from datetime import UTC, datetime

from rs_collector.jobs.models import JobKind, JobStatus, JobView


class Job:
    def __init__(self, identifier: str, kind: JobKind, title: str) -> None:
        self._id = identifier
        self._kind = kind
        self._title = title
        self._lock = threading.Lock()
        self._lines: list[str] = []
        self._status = JobStatus.RUNNING
        self._started_at = datetime.now(UTC)
        self._finished_at: datetime | None = None
        self._outcome = ""
        self._report_url = ""
        self.thread_id: int | None = None

    @property
    def id(self) -> str:
        return self._id

    def write(self, line: str) -> None:
        with self._lock:
            self._lines.append(line)

    def succeeded(self, outcome: str, report_url: str = "") -> None:
        self._finish(JobStatus.SUCCEEDED, outcome, report_url)

    def failed(self, outcome: str) -> None:
        self._finish(JobStatus.FAILED, outcome)

    def view(self, from_line: int = 0) -> JobView:
        with self._lock:
            return JobView(
                id=self._id,
                kind=self._kind,
                title=self._title,
                status=self._status,
                started_at=self._started_at,
                finished_at=self._finished_at,
                lines=tuple(self._lines[from_line:]),
                outcome=self._outcome,
                report_url=self._report_url,
            )

    def line_count(self) -> int:
        with self._lock:
            return len(self._lines)

    def _finish(self, status: JobStatus, outcome: str, report_url: str = "") -> None:
        with self._lock:
            self._status = status
            self._outcome = outcome
            self._report_url = report_url
            self._finished_at = datetime.now(UTC)
