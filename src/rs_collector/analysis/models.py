from datetime import datetime
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from rs_collector.analysis.options import AnalysisOptions


class AnalysisStatus(StrEnum):
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    TIMED_OUT = "timed_out"


class AnalysisMetadata(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str = Field(min_length=1)
    package_name: str = Field(min_length=1)
    cluster_fqdn: str = Field(min_length=1)
    environment: str = Field(default="")
    options: AnalysisOptions
    command: tuple[str, ...]
    analyzed_at: datetime
    finished_at: datetime | None = Field(default=None)
    duration_seconds: float | None = Field(default=None, ge=0)
    status: AnalysisStatus = Field(default=AnalysisStatus.RUNNING)
    exit_status: int | None = Field(default=None)
    pinned: bool = Field(default=False)

    def finished(
        self, status: AnalysisStatus, finished_at: datetime, exit_status: int | None
    ) -> AnalysisMetadata:
        return self.model_copy(
            update={
                "status": status,
                "finished_at": finished_at,
                "exit_status": exit_status,
                "duration_seconds": (finished_at - self.analyzed_at).total_seconds(),
            }
        )

    def with_pinned(self, pinned: bool) -> AnalysisMetadata:
        return self.model_copy(update={"pinned": pinned})


class StoredAnalysis(BaseModel):
    model_config = ConfigDict(frozen=True)

    metadata: AnalysisMetadata
    directory: Path

    @property
    def name(self) -> str:
        return self.metadata.name
