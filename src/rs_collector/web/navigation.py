from pydantic import BaseModel, ConfigDict, Field

_HOME = "/"


class Tool(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str = Field(min_length=1)
    path: str = Field(min_length=1)
    summary: str = Field(default="")


class Navigation(BaseModel):
    model_config = ConfigDict(frozen=True)

    tools: tuple[Tool, ...] = Field(default=())
    current: str = Field(default="")

    def here(self, path: str) -> Navigation:
        return self.model_copy(update={"current": path})

    def is_here(self, tool: Tool) -> bool:
        if tool.path == _HOME:
            return self.current == _HOME
        return self.current.startswith(tool.path.rstrip(_HOME))
