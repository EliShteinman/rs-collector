import gzip
import json
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
            "keep_colours": True,
            "live_log_name": "redisscope_current.log",
            "live_log_poll_seconds": 0.05,
        },
        "retention": {"max_age_days": 7},
        "serve": {
            "host": "0.0.0.0",
            "port": 3923,
            "base_path": "",
            "auth_realm": "rsc",
            "max_inline_bytes": 5_242_880,
            "max_log_lines": 5_000,
            "max_jobs": 50,
            "max_job_lines": 2_000,
        },
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
echo "RedisScope starting with: $@"
printf 'extracting the package'
printf '\r100%% extracted\n'
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


_RLADMIN_STATUS = """CLUSTER NODES:
NODE:ID   ROLE        ADDRESS      RACK-ID   STATUS
node:1    master      10.0.0.1               OK
node:2    slave       10.0.0.2               OK

DATABASES:
DB:ID     NAME        TYPE     STATUS   SHARDS   PLACEMENT
db:1      orders      redis    active   2        dense
db:2      sessions    redis    active   1        dense

SHARDS:
DB:ID     NAME        ID        NODE      ROLE     SLOTS       USED_MEMORY   STATUS
db:1      orders      redis:3   node:1    master   0-8191      2.1MB         OK
db:1      orders      redis:4   node:2    slave    0-8191      2.0MB         OK
db:2      sessions    redis:7   node:1    master   0-16383     1.4MB         OK
"""

_CCS = {
    "bdb:1": {"name": "orders", "redis_list": [3, 4], "crdt": False},
    "bdb:2": {"name": "sessions", "redis_list": [7], "crdt": True, "crdt_guid": "abc"},
    "node:1": {"uid": 1},
}


@pytest.fixture
def support_package(tmp_path: Path) -> Path:
    root = tmp_path / "redisscope_sp"
    for node in ("node_1", "node_2"):
        (root / node / "logs").mkdir(parents=True)
        (root / node / "conf").mkdir(parents=True)
    (root / "node_1" / "node_1.rladmin").write_text(_RLADMIN_STATUS, encoding="utf-8")
    (root / "node_1" / "ccs_redis.json").write_text(json.dumps(_CCS), encoding="utf-8")
    logs_one = root / "node_1" / "logs"
    logs_two = root / "node_2" / "logs"
    (logs_one / "redis_3.log").write_text(
        "3:M 23 Sep 2026 10:00:02.100 * newest line of shard 3\n", encoding="utf-8"
    )
    (logs_one / "redis_3.log.1").write_text(
        "3:M 23 Sep 2026 09:00:01.100 * older line of shard 3\n", encoding="utf-8"
    )
    (logs_one / "redis_3.log.2.gz").write_bytes(
        gzip.compress(b"3:M 23 Sep 2026 08:00:00.100 * oldest line of shard 3\n")
    )
    (logs_two / "redis_4.log").write_text(
        "4:S 23 Sep 2026 10:00:03.100 * line of shard 4\n", encoding="utf-8"
    )
    (logs_one / "redis_7.log").write_text(
        "7:M 23 Sep 2026 10:00:04.100 * line of shard 7\n", encoding="utf-8"
    )
    (logs_one / "crdt_syncer-2.log").write_text(
        "2026-09-23 10:00:05 - INFO - syncing from the remote cluster\n", encoding="utf-8"
    )
    (logs_one / "redis_mgr.log").write_text("not a shard log\n", encoding="utf-8")
    return root
