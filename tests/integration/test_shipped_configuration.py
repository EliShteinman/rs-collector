from pathlib import Path

import pytest

from rs_collector.logging_setup.configurator import LoggerFactory, LoggingConfigurator
from rs_collector.settings.loader import SettingsLoader
from rs_collector.settings.paths import ConfigPaths

pytestmark = pytest.mark.integration


def test_shipped_settings_file_is_valid(repo_config_paths: ConfigPaths) -> None:
    settings = SettingsLoader(repo_config_paths).load()

    assert settings.serve.port == 3923


def test_shipped_logging_file_writes_to_the_given_log_directory(
    repo_config_paths: ConfigPaths, tmp_path: Path
) -> None:
    log_dir = tmp_path / "logs"

    LoggingConfigurator(repo_config_paths).configure(log_dir)
    LoggerFactory.for_component("configuration").info("configuration loaded")

    assert (log_dir / "rsc.log").is_file()


def test_shipped_logging_file_records_debug_messages(
    repo_config_paths: ConfigPaths, tmp_path: Path
) -> None:
    log_dir = tmp_path / "logs"

    LoggingConfigurator(repo_config_paths).configure(log_dir)
    LoggerFactory.for_component("configuration").debug("detailed trace")

    assert "detailed trace" in (log_dir / "rsc.log").read_text(encoding="utf-8")
