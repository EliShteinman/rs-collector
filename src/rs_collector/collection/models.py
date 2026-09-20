from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from rs_collector.inventory.models import Cluster, Hostname


class RemotePackage(BaseModel):
    model_config = ConfigDict(frozen=True)

    path: str = Field(min_length=1)
    size_bytes: int = Field(ge=0)
    sha256: str = Field(min_length=64, max_length=64)

    @property
    def file_name(self) -> str:
        return Path(self.path).name


class CollectedPackage(BaseModel):
    model_config = ConfigDict(frozen=True)

    cluster: Cluster
    collected_from: Hostname
    collected_at: datetime
    local_path: Path
    size_bytes: int = Field(ge=0)
    sha256: str = Field(min_length=64, max_length=64)
