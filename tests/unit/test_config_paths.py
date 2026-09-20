from pathlib import Path

import pytest

from rs_collector.runtime.bundle import BundleLocator
from rs_collector.settings.paths import ConfigDirSettings, ConfigPaths, ConfigPathsResolver

pytestmark = pytest.mark.unit


def test_resolver_prefers_the_configured_directory(tmp_path: Path) -> None:
    resolver = ConfigPathsResolver(dir_settings=ConfigDirSettings(config_dir=tmp_path))

    assert resolver.resolve().config_dir == tmp_path


def test_resolver_falls_back_to_the_bundle_root(clean_environment: None) -> None:
    resolver = ConfigPathsResolver(dir_settings=ConfigDirSettings())

    assert resolver.resolve().config_dir == BundleLocator().root() / "config"


def test_paths_expose_every_configuration_file(tmp_path: Path) -> None:
    paths = ConfigPaths(config_dir=tmp_path)

    assert paths.settings_file.name == "settings.yml"
    assert paths.clusters_file.name == "clusters.yml"
    assert paths.logging_file.name == "logging.yml"


def test_a_blank_environment_variable_is_ignored(
    monkeypatch: pytest.MonkeyPatch, clean_environment: None
) -> None:
    monkeypatch.setenv("RSC_CONFIG_DIR", "  ")

    assert ConfigPathsResolver().resolve().config_dir == BundleLocator().root() / "config"


def test_the_env_file_sits_next_to_the_configuration_directory(tmp_path: Path) -> None:
    assert ConfigPaths(config_dir=tmp_path / "config").env_file == tmp_path / "rsc.env"
