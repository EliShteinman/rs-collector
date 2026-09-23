import logging
import threading

from rs_collector.jobs.job import Job

_FORMAT = "%(levelname)-8s %(message)s"
_NAMESPACE = "rs_collector"


class JobLogHandler(logging.Handler):
    def __init__(self, job: Job, level: int = logging.INFO) -> None:
        super().__init__(level)
        self._job = job
        self.setFormatter(logging.Formatter(_FORMAT))

    def emit(self, record: logging.LogRecord) -> None:
        if record.thread != self._job.thread_id:
            return
        self._job.write(self.format(record))


class JobLogCapture:
    def __init__(self, job: Job, namespace: str = _NAMESPACE) -> None:
        self._handler = JobLogHandler(job)
        self._logger = logging.getLogger(namespace)
        self._job = job

    def __enter__(self) -> None:
        self._job.thread_id = threading.get_ident()
        self._logger.addHandler(self._handler)

    def __exit__(self, *_: object) -> None:
        self._logger.removeHandler(self._handler)
