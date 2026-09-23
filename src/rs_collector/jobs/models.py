from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class JobStatus(StrEnum):
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class JobKind(StrEnum):
    COLLECT = "collect"
    ANALYZE = "analyze"


class JobView(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    kind: JobKind
    title: str
    status: JobStatus
    started_at: datetime
    finished_at: datetime | None = Field(default=None)
    lines: tuple[str, ...] = Field(default=())
    next_line: int = Field(default=0, ge=0)
    outcome: str = Field(default="")
    report_url: str = Field(default="")

    @property
    def is_running(self) -> bool:
        return self.status is JobStatus.RUNNING
