import threading
from collections import deque
from datetime import UTC, datetime

from rs_collector.jobs.models import JobKind, JobStatus, JobView


class Job:
    def __init__(self, identifier: str, kind: JobKind, title: str, max_lines: int) -> None:
        self._id = identifier
        self._kind = kind
        self._title = title
        self._lock = threading.Lock()
        self._lines: deque[str] = deque(maxlen=max_lines)
        self._written = 0
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
            self._written += 1

    def succeeded(self, outcome: str, report_url: str = "") -> None:
        self._finish(JobStatus.SUCCEEDED, outcome, report_url)

    def failed(self, outcome: str) -> None:
        self._finish(JobStatus.FAILED, outcome)

    def view(self, from_line: int = 0) -> JobView:
        with self._lock:
            kept = list(self._lines)
            first = self._written - len(kept)
            return JobView(
                id=self._id,
                kind=self._kind,
                title=self._title,
                status=self._status,
                started_at=self._started_at,
                finished_at=self._finished_at,
                lines=tuple(kept[max(0, from_line - first) :]),
                next_line=self._written,
                outcome=self._outcome,
                report_url=self._report_url,
            )

    def _finish(self, status: JobStatus, outcome: str, report_url: str = "") -> None:
        with self._lock:
            self._status = status
            self._outcome = outcome
            self._report_url = report_url
            self._finished_at = datetime.now(UTC)
