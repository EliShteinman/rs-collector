from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml

from rs_collector.cli.container import Container
from rs_collector.packages.models import PackageMetadata
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
            "logs_dir_name": "logs",
            "package_archive_name": "support_package.tar.gz",
            "package_metadata_name": "package.json",
            "analysis_metadata_name": "analysis.json",
            "cleanup_history_name": "last_cleanup.json",
        },
        "remote": {
            "rladmin_path": "/opt/redislabs/bin/rladmin",
            "remote_tmp_dir": "/tmp",
            "connect_timeout_seconds": 10,
            "command_timeout_seconds": 60,
            "debug_info_timeout_seconds": 1800,
            "auto_accept_host_keys": True,
            "known_hosts_file_name": "known_hosts",
            "sudo_prompt_wait_seconds": 5,
            "root_prompt_timeout_seconds": 30,
        },
        "analysis": {
            "redisscope_binary": "/opt/redisscope/redisscope",
            "timeout_seconds": 7200,
            "console_log_name": "analysis_console.log",
        },
        "retention": {"max_age_days": 7},
        "serve": {"host": "0.0.0.0", "port": 3923, "base_path": ""},
        "background": {
            "pid_file_name": "serve.pid",
            "console_log_name": "serve_console.log",
            "startup_check_seconds": 0.5,
            "stop_timeout_seconds": 5,
            "cleanup_schedule": "30 3 * * *",
            "crontab_marker": "# rsc",
        },
    }


@pytest.fixture(autouse=True)
def data_root_environment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    data_root = tmp_path / "data"
    monkeypatch.setenv("RSC_DATA_ROOT", str(data_root))
    return data_root


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


_FAKE_ANALYZER = """#!/bin/sh
mkdir -p redisscope_html
echo "<html>the report</html>" > redisscope_html/report.html
"""


@pytest.fixture
def analyzer(tmp_path: Path) -> Path:
    path = tmp_path / "redisscope"
    path.write_text(_FAKE_ANALYZER, encoding="utf-8")
    path.chmod(0o755)
    return path


@pytest.fixture
def web_paths(tmp_path: Path, settings_document: dict[str, object], analyzer: Path) -> ConfigPaths:
    config_dir = tmp_path / "web-config"
    config_dir.mkdir()
    paths = ConfigPaths(config_dir=config_dir)
    document = dict(settings_document)
    document["analysis"] = {**settings_document["analysis"], "redisscope_binary": str(analyzer)}
    paths.settings_file.write_text(yaml.safe_dump(document), encoding="utf-8")
    paths.clusters_file.write_text(
        yaml.safe_dump({"environments": {"production": [{"fqdn": "c1.example.com"}]}}),
        encoding="utf-8",
    )
    paths.logging_file.write_text(
        yaml.safe_dump({"version": 1, "disable_existing_loggers": False}), encoding="utf-8"
    )
    return paths


@pytest.fixture
def container(web_paths: ConfigPaths) -> Container:
    return Container(paths=web_paths)


@pytest.fixture
def package(container: Container) -> str:
    metadata = PackageMetadata(
        name="c1.example.com__2026-09-23_10-00-00",
        cluster_fqdn="c1.example.com",
        environment="production",
        collected_from="n1.c1.example.com",
        collected_at=datetime.now(UTC),
        original_file_name="debuginfo.tar.gz",
        size_bytes=1024,
        sha256="a" * 64,
    )
    stored = container.packages().save(metadata)
    stored.archive_path.write_bytes(b"payload")
    return stored.name
