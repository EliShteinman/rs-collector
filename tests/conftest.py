from collections.abc import Iterator
from pathlib import Path

import pytest

from rs_collector.settings.models import AppSettings
from rs_collector.settings.paths import ConfigPaths

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def repo_config_paths() -> ConfigPaths:
    return ConfigPaths(config_dir=REPO_ROOT / "config")


@pytest.fixture
def config_dir(tmp_path: Path) -> Path:
    directory = tmp_path / "config"
    directory.mkdir()
    return directory


@pytest.fixture
def config_paths(config_dir: Path) -> ConfigPaths:
    return ConfigPaths(config_dir=config_dir)


@pytest.fixture
def settings_document(tmp_path: Path) -> dict[str, object]:
    return {
        "storage": {
            "data_root": str(tmp_path / "data"),
            "packages_dir_name": "packages",
            "analyses_dir_name": "analyses",
            "locks_dir_name": "locks",
        },
        "remote": {
            "rladmin_path": "/opt/redislabs/bin/rladmin",
            "remote_tmp_dir": "/tmp",
            "connect_timeout_seconds": 10,
            "command_timeout_seconds": 60,
            "debug_info_timeout_seconds": 1800,
            "auto_accept_host_keys": True,
            "root_prompt_timeout_seconds": 30,
        },
        "analysis": {
            "redisscope_binary": "/opt/redisscope/redisscope",
            "timeout_seconds": 7200,
            "console_log_name": "analysis_console.log",
        },
        "retention": {"max_age_days": 7},
        "serve": {"host": "0.0.0.0", "port": 3923, "share_name": "analyses"},
    }


@pytest.fixture
def app_settings(settings_document: dict[str, object]) -> AppSettings:
    return AppSettings.model_validate(settings_document)


@pytest.fixture
def clean_environment(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    for name in (
        "RSC_SSH_USER",
        "RSC_SSH_KEY_PATH",
        "RSC_SSH_PASSWORD",
        "RSC_SUDO_PASSWORD",
        "RSC_CONFIG_DIR",
    ):
        monkeypatch.delenv(name, raising=False)
    yield
