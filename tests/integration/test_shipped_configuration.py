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


def test_a_settings_file_from_an_older_release_still_loads(
    repo_config_paths: ConfigPaths, config_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    shipped = (repo_config_paths.settings_file).read_text(encoding="utf-8")
    without_the_new_key = "\n".join(
        line for line in shipped.splitlines() if "auth_realm" not in line
    )
    (config_dir / "settings.yml").write_text(without_the_new_key, encoding="utf-8")
    monkeypatch.setenv("RSC_DATA_ROOT", str(config_dir.parent / "data"))

    assert SettingsLoader(ConfigPaths(config_dir=config_dir)).load().serve.auth_realm == "rsc"
