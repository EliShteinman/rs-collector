from datetime import UTC, datetime
from pathlib import Path

import pytest
from tests.fakes import FakeProcessRunner

from rs_collector.analysis.models import AnalysisStatus
from rs_collector.analysis.options import AnalysisDepth, AnalysisOptions
from rs_collector.analysis.repository import AnalysisRepository
from rs_collector.analysis.runner import RedisScopeRunner
from rs_collector.exceptions.analysis import (
    AnalysisFailedError,
    AnalysisTimeoutError,
    AnalyzerStartError,
)
from rs_collector.exceptions.processes import ProcessStartError, ProcessTimeoutError
from rs_collector.packages.models import PackageMetadata, StoredPackage
from rs_collector.settings.models import AppSettings

pytestmark = pytest.mark.unit


@pytest.fixture
def package(app_settings: AppSettings) -> StoredPackage:
    directory = app_settings.storage.packages_dir / "c1.example.com__2026-09-19_14-30-05"
    directory.mkdir(parents=True)
    archive = directory / "support_package.tar.gz"
    archive.write_bytes(b"payload")
    return StoredPackage(
        metadata=PackageMetadata(
            name=directory.name,
            cluster_fqdn="c1.example.com",
            environment="production",
            collected_from="n1.c1.example.com",
            collected_at=datetime(2026, 9, 19, 14, 30, 5, tzinfo=UTC),
            original_file_name="debuginfo.tar.gz",
            size_bytes=7,
            sha256="a" * 64,
        ),
        directory=directory,
        archive_path=archive,
    )


def _runner(app_settings: AppSettings, processes: FakeProcessRunner) -> RedisScopeRunner:
    return RedisScopeRunner(
        AnalysisRepository(app_settings.storage),
        app_settings.analysis,
        app_settings.storage,
        processes,
    )


def test_analyze_creates_the_analysis_directory(
    app_settings: AppSettings, package: StoredPackage
) -> None:
    stored = _runner(app_settings, FakeProcessRunner()).analyze(package, AnalysisOptions())

    assert stored.directory.is_dir()


def test_analyze_names_the_directory_after_the_package_and_options(
    app_settings: AppSettings, package: StoredPackage
) -> None:
    options = AnalysisOptions(bdb_id=5, depth=AnalysisDepth.MAX, mask=True)

    stored = _runner(app_settings, FakeProcessRunner()).analyze(package, options)

    assert stored.name == f"{package.name}__bdb-5__max__masked"


def test_analyze_runs_redisscope_in_the_analysis_directory(
    app_settings: AppSettings, package: StoredPackage
) -> None:
    processes = FakeProcessRunner()

    stored = _runner(app_settings, processes).analyze(package, AnalysisOptions())

    assert processes.calls[0][1] == stored.directory


def test_analyze_points_redisscope_at_the_stored_archive(
    app_settings: AppSettings, package: StoredPackage
) -> None:
    processes = FakeProcessRunner()

    _runner(app_settings, processes).analyze(package, AnalysisOptions())

    assert processes.calls[0][0] == (
        "/opt/redisscope/redisscope",
        "--sp",
        str(package.archive_path),
    )


def test_analyze_writes_the_console_log(app_settings: AppSettings, package: StoredPackage) -> None:
    stored = _runner(app_settings, FakeProcessRunner()).analyze(package, AnalysisOptions())

    assert (stored.directory / "analysis_console.log").is_file()


def test_analyze_records_a_successful_status(
    app_settings: AppSettings, package: StoredPackage
) -> None:
    stored = _runner(app_settings, FakeProcessRunner()).analyze(package, AnalysisOptions())

    assert stored.metadata.status is AnalysisStatus.SUCCEEDED


def test_analyze_records_the_duration(app_settings: AppSettings, package: StoredPackage) -> None:
    stored = _runner(app_settings, FakeProcessRunner()).analyze(package, AnalysisOptions())

    assert stored.metadata.duration_seconds >= 0


def test_a_failing_analyzer_is_reported(app_settings: AppSettings, package: StoredPackage) -> None:
    with pytest.raises(AnalysisFailedError):
        _runner(app_settings, FakeProcessRunner(exit_status=2)).analyze(package, AnalysisOptions())


def test_a_failing_analyzer_leaves_a_failed_status(
    app_settings: AppSettings, package: StoredPackage
) -> None:
    runner = _runner(app_settings, FakeProcessRunner(exit_status=2))
    repository = AnalysisRepository(app_settings.storage)

    with pytest.raises(AnalysisFailedError):
        runner.analyze(package, AnalysisOptions())

    assert repository.list()[0].metadata.status is AnalysisStatus.FAILED


def test_a_timed_out_analyzer_leaves_a_timed_out_status(
    app_settings: AppSettings, package: StoredPackage
) -> None:
    runner = _runner(app_settings, FakeProcessRunner(error=ProcessTimeoutError("too slow")))
    repository = AnalysisRepository(app_settings.storage)

    with pytest.raises(AnalysisTimeoutError):
        runner.analyze(package, AnalysisOptions())

    assert repository.list()[0].metadata.status is AnalysisStatus.TIMED_OUT


def test_an_analyzer_that_cannot_start_is_reported(
    app_settings: AppSettings, package: StoredPackage
) -> None:
    runner = _runner(app_settings, FakeProcessRunner(error=ProcessStartError("permission denied")))

    with pytest.raises(AnalyzerStartError):
        runner.analyze(package, AnalysisOptions())


def test_a_repeated_analysis_gets_its_own_directory(
    app_settings: AppSettings, package: StoredPackage
) -> None:
    runner = _runner(app_settings, FakeProcessRunner())
    first = runner.analyze(package, AnalysisOptions())

    second = runner.analyze(package, AnalysisOptions())

    assert second.name == f"{first.name}__2"


def test_a_real_unexecutable_analyzer_is_reported_as_a_start_failure(
    tmp_path: Path, app_settings: AppSettings, package: StoredPackage
) -> None:
    analyzer = tmp_path / "redisscope"
    analyzer.write_text("#!/bin/sh\n", encoding="utf-8")
    analyzer.chmod(0o644)
    settings = app_settings.analysis.model_copy(update={"redisscope_binary": analyzer})
    runner = RedisScopeRunner(
        AnalysisRepository(app_settings.storage), settings, app_settings.storage
    )

    with pytest.raises(AnalyzerStartError, match="Permission denied"):
        runner.analyze(package, AnalysisOptions())
