from datetime import UTC, datetime
from pathlib import Path

import pytest

from rs_collector.analysis.options import AnalysisDepth, AnalysisOptions
from rs_collector.analysis.repository import AnalysisRepository
from rs_collector.analysis.runner import RedisScopeRunner
from rs_collector.exceptions.analysis import AnalysisFailedError
from rs_collector.packages.models import PackageMetadata, StoredPackage
from rs_collector.settings.models import AnalysisSettings, AppSettings

pytestmark = pytest.mark.integration

_FAKE_ANALYZER = """#!/bin/sh
echo "args: $@"
mkdir -p redisscope_html redisscope_sp redisscope_logs
echo "<html>report</html>" > redisscope_html/report.html
exit ${RSC_TEST_EXIT:-0}
"""


@pytest.fixture
def analyzer(tmp_path: Path) -> Path:
    path = tmp_path / "redisscope"
    path.write_text(_FAKE_ANALYZER, encoding="utf-8")
    path.chmod(0o755)
    return path


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
            collected_from="n1.c1.example.com",
            collected_at=datetime(2026, 9, 19, 14, 30, 5, tzinfo=UTC),
            original_file_name="debuginfo.tar.gz",
            size_bytes=7,
            sha256="a" * 64,
        ),
        directory=directory,
        archive_path=archive,
    )


def _runner(app_settings: AppSettings, analyzer: Path, timeout: int = 60) -> RedisScopeRunner:
    settings = AnalysisSettings(
        redisscope_binary=analyzer,
        timeout_seconds=timeout,
        console_log_name=app_settings.analysis.console_log_name,
    )
    return RedisScopeRunner(
        AnalysisRepository(app_settings.storage), settings, app_settings.storage
    )


def test_the_report_is_written_inside_the_analysis_directory(
    app_settings: AppSettings, analyzer: Path, package: StoredPackage
) -> None:
    stored = _runner(app_settings, analyzer).analyze(package, AnalysisOptions())

    assert (stored.directory / "redisscope_html" / "report.html").is_file()


def test_the_extracted_package_stays_in_the_analysis_directory(
    app_settings: AppSettings, analyzer: Path, package: StoredPackage
) -> None:
    stored = _runner(app_settings, analyzer).analyze(package, AnalysisOptions())

    assert (stored.directory / "redisscope_sp").is_dir()


def test_the_console_log_holds_the_analyzer_output(
    app_settings: AppSettings, analyzer: Path, package: StoredPackage
) -> None:
    options = AnalysisOptions(bdb_id=5, depth=AnalysisDepth.QUICK)

    stored = _runner(app_settings, analyzer).analyze(package, options)

    log = (stored.directory / "analysis_console.log").read_text(encoding="utf-8")
    assert "--bdb 5 --skiplogs" in log


def test_the_metadata_survives_a_failed_run(
    app_settings: AppSettings,
    analyzer: Path,
    package: StoredPackage,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RSC_TEST_EXIT", "3")

    with pytest.raises(AnalysisFailedError):
        _runner(app_settings, analyzer).analyze(package, AnalysisOptions())

    assert AnalysisRepository(app_settings.storage).list()[0].metadata.exit_status == 3
