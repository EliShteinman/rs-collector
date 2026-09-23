import sys

import pytest

from rs_collector.runtime.environment import SpawnEnvironment

pytestmark = pytest.mark.unit


def test_the_bundle_variables_are_dropped() -> None:
    cleaned = SpawnEnvironment(
        {"PATH": "/usr/bin", "_PYI_APPLICATION_HOME_DIR": "/tmp/_MEI123"}
    ).for_a_new_process()

    assert cleaned == {"PATH": "/usr/bin"}


def test_the_original_library_path_comes_back() -> None:
    cleaned = SpawnEnvironment(
        {"LD_LIBRARY_PATH": "/tmp/_MEI123", "LD_LIBRARY_PATH_ORIG": "/opt/lib"}
    ).for_a_new_process()

    assert cleaned == {"LD_LIBRARY_PATH": "/opt/lib"}


def test_the_bundle_library_path_is_dropped(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "_MEIPASS", "/tmp/_MEI123", raising=False)

    cleaned = SpawnEnvironment({"LD_LIBRARY_PATH": "/tmp/_MEI123"}).for_a_new_process()

    assert cleaned == {}


def test_an_unrelated_library_path_is_kept(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "_MEIPASS", "/tmp/_MEI123", raising=False)

    cleaned = SpawnEnvironment({"LD_LIBRARY_PATH": "/opt/lib"}).for_a_new_process()

    assert cleaned == {"LD_LIBRARY_PATH": "/opt/lib"}
