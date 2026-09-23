from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class Shard(BaseModel):
    model_config = ConfigDict(frozen=True)

    uid: str = Field(min_length=1)
    node: str = Field(default="")
    role: str = Field(default="")


class Database(BaseModel):
    model_config = ConfigDict(frozen=True)

    uid: str = Field(min_length=1)
    name: str = Field(default="")
    shards: tuple[Shard, ...] = Field(default=())
    active_active: bool = Field(default=False)

    def answers_to(self, asked: str) -> bool:
        wanted = asked.strip().lower()
        return wanted in (self.uid.lower(), self.name.lower())


class LogFile(BaseModel):
    model_config = ConfigDict(frozen=True)

    path: Path
    node: str = Field(default="")
    rotation: int = Field(default=0, ge=0)
    compressed: bool = Field(default=False)


class MergedLog(BaseModel):
    model_config = ConfigDict(frozen=True)

    title: str
    path: Path
    sources: tuple[Path, ...] = Field(default=())
    lines: int = Field(default=0, ge=0)
    byte_count: int = Field(default=0, ge=0)
    node: str = Field(default="")
    role: str = Field(default="")
    first_seen: datetime | None = Field(default=None)
    last_seen: datetime | None = Field(default=None)


class PackageFile(BaseModel):
    model_config = ConfigDict(frozen=True)

    path: Path
    byte_count: int = Field(default=0, ge=0)


class DatabaseLogs(BaseModel):
    model_config = ConfigDict(frozen=True)

    database: Database
    shard_logs: tuple[MergedLog, ...] = Field(default=())
    sync_logs: tuple[MergedLog, ...] = Field(default=())
    package_files: tuple[PackageFile, ...] = Field(default=())

    @property
    def merged(self) -> tuple[MergedLog, ...]:
        return (*self.shard_logs, *self.sync_logs)
