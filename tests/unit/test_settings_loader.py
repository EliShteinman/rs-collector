from pathlib import Path

import pytest
import yaml

from rs_collector.exceptions.configuration import (
    ConfigFileFormatError,
    ConfigFileNotFoundError,
    ConfigValidationError,
    MissingSettingError,
)
from rs_collector.settings.loader import SettingsLoader
from rs_collector.settings.paths import ConfigPaths

pytestmark = pytest.mark.unit


def _write_settings(paths: ConfigPaths, document: object) -> None:
    paths.settings_file.write_text(yaml.safe_dump(document), encoding="utf-8")


def test_load_returns_settings_for_a_valid_document(
    config_paths: ConfigPaths, settings_document: dict[str, object]
) -> None:
    _write_settings(config_paths, settings_document)

    settings = SettingsLoader(config_paths).load()

    assert settings.retention.max_age_days == 7


def test_load_resolves_the_packages_directory(
    config_paths: ConfigPaths, settings_document: dict[str, object], tmp_path: Path
) -> None:
    _write_settings(config_paths, settings_document)

    settings = SettingsLoader(config_paths).load()

    assert settings.storage.packages_dir == tmp_path / "data" / "packages"


def test_load_rejects_a_missing_file(config_paths: ConfigPaths) -> None:
    with pytest.raises(ConfigFileNotFoundError):
        SettingsLoader(config_paths).load()


def test_load_rejects_a_document_that_is_not_a_mapping(config_paths: ConfigPaths) -> None:
    config_paths.settings_file.write_text("- one\n- two\n", encoding="utf-8")

    with pytest.raises(ConfigFileFormatError):
        SettingsLoader(config_paths).load()


def test_load_rejects_broken_yaml(config_paths: ConfigPaths) -> None:
    config_paths.settings_file.write_text("storage: [\n", encoding="utf-8")

    with pytest.raises(ConfigFileFormatError):
        SettingsLoader(config_paths).load()


def test_load_rejects_an_unknown_section(
    config_paths: ConfigPaths, settings_document: dict[str, object]
) -> None:
    _write_settings(config_paths, {**settings_document, "unknown": {}})

    with pytest.raises(ConfigValidationError):
        SettingsLoader(config_paths).load()


def test_load_rejects_a_non_positive_retention(
    config_paths: ConfigPaths, settings_document: dict[str, object]
) -> None:
    _write_settings(config_paths, {**settings_document, "retention": {"max_age_days": 0}})

    with pytest.raises(ConfigValidationError):
        SettingsLoader(config_paths).load()


def test_the_data_root_comes_from_the_environment(
    config_paths: ConfigPaths,
    settings_document: dict[str, object],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _write_settings(config_paths, settings_document)
    monkeypatch.setenv("RSC_DATA_ROOT", str(tmp_path / "company-disk"))

    assert SettingsLoader(config_paths).load().storage.data_root == tmp_path / "company-disk"


def test_the_data_root_can_come_from_the_env_file(
    config_paths: ConfigPaths,
    settings_document: dict[str, object],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _write_settings(config_paths, settings_document)
    monkeypatch.delenv("RSC_DATA_ROOT")
    config_paths.env_file.write_text(f"RSC_DATA_ROOT={tmp_path / 'from-file'}\n", encoding="utf-8")

    assert SettingsLoader(config_paths).load().storage.data_root == tmp_path / "from-file"


def test_a_missing_data_root_is_reported(
    config_paths: ConfigPaths, settings_document: dict[str, object], monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_settings(config_paths, settings_document)
    monkeypatch.delenv("RSC_DATA_ROOT")

    with pytest.raises(MissingSettingError):
        SettingsLoader(config_paths).load()
