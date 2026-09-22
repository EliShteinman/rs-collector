from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class RemoteSettings(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    rladmin_path: str = Field(description="Absolute path of rladmin on the cluster nodes")
    remote_tmp_dir: str = Field(description="Remote directory the support package is written to")
    connect_timeout_seconds: int = Field(gt=0)
    command_timeout_seconds: int = Field(gt=0)
    debug_info_timeout_seconds: int = Field(gt=0)
    auto_accept_host_keys: bool = Field(default=True)
    sudo_prompt_wait_seconds: int = Field(gt=0)
    root_prompt_timeout_seconds: int = Field(gt=0)


class AnalysisSettings(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    redisscope_binary: Path = Field(description="Absolute path of the RedisScope executable")
    timeout_seconds: int = Field(gt=0)
    console_log_name: str = Field(description="File the analyzer output is written to")


class RetentionSettings(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    max_age_days: int = Field(gt=0)


class ServeSettings(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    host: str
    port: int = Field(gt=0, lt=65536)
    share_name: str


class BackgroundSettings(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    pid_file_name: str = Field(description="File in the locks directory holding the server PID")
    console_log_name: str = Field(description="File in the logs directory for the server output")
    startup_check_seconds: float = Field(gt=0)
    stop_timeout_seconds: float = Field(gt=0)
    cleanup_schedule: str = Field(description="Cron schedule of the daily cleanup")
    crontab_marker: str = Field(description="Comment marking the crontab lines rsc owns")


class StorageSettings(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    data_root: Path
    packages_dir_name: str
    analyses_dir_name: str
    locks_dir_name: str
    package_archive_name: str
    package_metadata_name: str
    analysis_metadata_name: str

    @property
    def packages_dir(self) -> Path:
        return self.data_root / self.packages_dir_name

    @property
    def analyses_dir(self) -> Path:
        return self.data_root / self.analyses_dir_name

    @property
    def locks_dir(self) -> Path:
        return self.data_root / self.locks_dir_name


class AppSettings(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    storage: StorageSettings
    remote: RemoteSettings
    analysis: AnalysisSettings
    retention: RetentionSettings
    serve: ServeSettings
    background: BackgroundSettings
