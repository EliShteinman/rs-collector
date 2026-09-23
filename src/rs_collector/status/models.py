from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

_BYTES_PER_GIB = 1_073_741_824


class ServerStatus(BaseModel):
    model_config = ConfigDict(frozen=True)

    host: str
    port: int
    pid: int | None = Field(default=None)

    @property
    def is_running(self) -> bool:
        return self.pid is not None


class ScheduleStatus(BaseModel):
    model_config = ConfigDict(frozen=True)

    starts_after_reboot: bool
    cleanup_schedule: str
    cleanup_last_run: datetime | None = Field(default=None)
    removed_last_run: int = Field(default=0, ge=0)
    keeps_days: int = Field(gt=0)


class StorageStatus(BaseModel):
    model_config = ConfigDict(frozen=True)

    data_root: Path
    free_bytes: int = Field(ge=0)
    total_bytes: int = Field(ge=0)
    packages: int = Field(ge=0)
    packages_bytes: int = Field(ge=0)
    analyses: int = Field(ge=0)
    pinned: int = Field(ge=0)

    @property
    def free_gib(self) -> float:
        return self.free_bytes / _BYTES_PER_GIB

    @property
    def total_gib(self) -> float:
        return self.total_bytes / _BYTES_PER_GIB

    @property
    def used_share(self) -> float:
        if self.total_bytes == 0:
            return 0.0
        return (self.total_bytes - self.free_bytes) / self.total_bytes


class SystemStatus(BaseModel):
    model_config = ConfigDict(frozen=True)

    server: ServerStatus
    schedule: ScheduleStatus
    storage: StorageStatus
