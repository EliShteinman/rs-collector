import sys
from pathlib import Path

import pytest

from rs_collector.runtime.bundle import BundleLocator

pytestmark = pytest.mark.unit


def test_a_source_checkout_uses_the_repository_root() -> None:
    assert (BundleLocator().root() / "pyproject.toml").is_file()


def test_the_packaged_executable_uses_its_own_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path / "extracted"), raising=False)

    assert BundleLocator(executable=str(tmp_path / "rsc")).root() == tmp_path
