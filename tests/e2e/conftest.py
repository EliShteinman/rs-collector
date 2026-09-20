from pathlib import Path

import pytest
import yaml

from rs_collector.settings.paths import ConfigPaths

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def deployment(tmp_path: Path, settings_document: dict[str, object]) -> ConfigPaths:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    paths = ConfigPaths(config_dir=config_dir)
    paths.settings_file.write_text(yaml.safe_dump(settings_document), encoding="utf-8")
    paths.clusters_file.write_text(
        yaml.safe_dump(
            {
                "environments": {
                    "production": [
                        {
                            "fqdn": "c1.example.com",
                            "nodes": ["n1.c1.example.com", "n2.c1.example.com"],
                        }
                    ]
                }
            }
        ),
        encoding="utf-8",
    )
    paths.logging_file.write_text(
        (REPO_ROOT / "config" / "logging.yml").read_text(encoding="utf-8"), encoding="utf-8"
    )
    return paths
