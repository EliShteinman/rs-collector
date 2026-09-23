from rs_collector.exceptions.jobs import JobError
from rs_collector.jobs.job import Job


class JobConsole:
    def __init__(self, job: Job) -> None:
        self._job = job

    def write(self, message: str) -> None:
        self._job.write(message)

    def read(self, prompt: str) -> str:
        raise JobError(f"A background job cannot answer a prompt: {prompt!r}")
