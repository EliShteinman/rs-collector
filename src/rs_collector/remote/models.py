from pydantic import BaseModel, ConfigDict, Field

from rs_collector.inventory.models import Hostname

_SUCCESS_STATUS = 0


class SshTarget(BaseModel):
    model_config = ConfigDict(frozen=True)

    host: Hostname
    port: int = Field(default=22, gt=0, lt=65536)
    username: str = Field(min_length=1)


class CommandResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    command: str
    exit_status: int
    output: str = Field(default="")

    @property
    def succeeded(self) -> bool:
        return self.exit_status == _SUCCESS_STATUS

    def first_line(self) -> str:
        return self.output.strip().splitlines()[0] if self.output.strip() else ""
