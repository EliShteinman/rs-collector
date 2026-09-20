from datetime import UTC, datetime, timedelta

import pytest

from rs_collector.cli.app import CliApplication
from rs_collector.cli.container import Container
from rs_collector.console.io import ScriptedConsole
from rs_collector.packages.models import PackageMetadata
from rs_collector.settings.paths import ConfigPaths

pytestmark = pytest.mark.e2e


def _package(name: str, age_days: int, pinned: bool = False) -> PackageMetadata:
    return PackageMetadata(
        name=name,
        cluster_fqdn="c1.example.com",
        environment="production",
        collected_from="n1.c1.example.com",
        collected_at=datetime.now(UTC) - timedelta(days=age_days),
        original_file_name="debuginfo.tar.gz",
        size_bytes=2_097_152,
        sha256="a" * 64,
        pinned=pinned,
    )


class CliHarness:
    def __init__(self, paths: ConfigPaths) -> None:
        self.console = ScriptedConsole([])
        self.container = Container(paths=paths, console=self.console)
        self._application = CliApplication(self.console, lambda _: self.container)

    def run(self, *argv: str) -> int:
        return self._application.run(argv)

    @property
    def output(self) -> str:
        return "\n".join(self.console.written)


@pytest.fixture
def cli(deployment: ConfigPaths) -> CliHarness:
    return CliHarness(deployment)


def test_list_reports_an_empty_store(cli: CliHarness) -> None:
    cli.run("list")

    assert "Packages (0):" in cli.output


def test_list_shows_a_stored_package(cli: CliHarness) -> None:
    cli.container.packages().save(_package("c1.example.com__2026-09-19_14-30-05", age_days=1))

    cli.run("list")

    assert "c1.example.com__2026-09-19_14-30-05  2.0 MiB" in cli.output


def test_pin_marks_a_package(cli: CliHarness) -> None:
    cli.container.packages().save(_package("kept", age_days=1))

    cli.run("pin", "kept")

    assert cli.container.packages().get("kept").metadata.pinned


def test_unpin_clears_the_mark(cli: CliHarness) -> None:
    cli.container.packages().save(_package("kept", age_days=1, pinned=True))

    cli.run("unpin", "kept")

    assert not cli.container.packages().get("kept").metadata.pinned


def test_pinning_an_unknown_name_fails_with_exit_code_one(cli: CliHarness) -> None:
    assert cli.run("pin", "missing") == 1


def test_a_dry_run_only_reports(cli: CliHarness) -> None:
    cli.container.packages().save(_package("old", age_days=9))

    cli.run("cleanup", "--dry-run")

    assert "Would remove package old" in cli.output


def test_cleanup_removes_an_expired_package(cli: CliHarness) -> None:
    cli.container.packages().save(_package("old", age_days=9))

    cli.run("cleanup")

    assert cli.container.packages().list() == ()


def test_cleanup_keeps_a_pinned_package(cli: CliHarness) -> None:
    cli.container.packages().save(_package("kept", age_days=90, pinned=True))

    cli.run("cleanup")

    assert len(cli.container.packages().list()) == 1


def test_the_log_file_is_written_next_to_the_data(cli: CliHarness) -> None:
    cli.run("list")

    assert (cli.container.log_dir / "rsc.log").is_file()
