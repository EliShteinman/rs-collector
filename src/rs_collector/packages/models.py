from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class PackageMetadata(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str = Field(min_length=1)
    cluster_fqdn: str = Field(min_length=1)
    environment: str = Field(default="")
    collected_from: str = Field(min_length=1)
    collected_at: datetime
    original_file_name: str = Field(min_length=1)
    size_bytes: int = Field(ge=0)
    sha256: str = Field(min_length=64, max_length=64)
    pinned: bool = Field(default=False)

    def with_pinned(self, pinned: bool) -> PackageMetadata:
        return self.model_copy(update={"pinned": pinned})


class StoredPackage(BaseModel):
    model_config = ConfigDict(frozen=True)

    metadata: PackageMetadata
    directory: Path
    archive_path: Path

    @property
    def name(self) -> str:
        return self.metadata.name


class PackageSlot(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str = Field(min_length=1)
    directory: Path
    archive_path: Path
