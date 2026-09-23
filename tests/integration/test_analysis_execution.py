import time
from datetime import UTC, datetime
from pathlib import Path

import pytest

from rs_collector.analysis.models import AnalysisStatus
from rs_collector.analysis.options import AnalysisDepth, AnalysisOptions
from rs_collector.analysis.repository import AnalysisRepository
from rs_collector.analysis.runner import RedisScopeRunner
from rs_collector.exceptions.analysis import AnalysisFailedError, AnalysisTimeoutError
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


_TALKATIVE_ANALYZER = """#!/bin/sh
echo "starting"
sleep 0.4
echo "finished"
mkdir -p redisscope_html
"""

_STUCK_ANALYZER = """#!/bin/sh
sleep 30
"""


def _script(tmp_path: Path, name: str, body: str) -> Path:
    path = tmp_path / name
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)
    return path


def test_the_analyzer_output_reaches_the_caller(
    app_settings: AppSettings, package: StoredPackage, analyzer: Path
) -> None:
    lines: list[str] = []
    runner = RedisScopeRunner(
        AnalysisRepository(app_settings.storage),
        AnalysisSettings(
            redisscope_binary=analyzer,
            timeout_seconds=60,
            console_log_name=app_settings.analysis.console_log_name,
        ),
        app_settings.storage,
        on_line=lambda text, _: lines.append(text),
    )

    runner.analyze(package, AnalysisOptions())

    assert any(line.startswith("args:") for line in lines)


def test_the_output_arrives_while_the_analyzer_still_runs(
    app_settings: AppSettings, package: StoredPackage, tmp_path: Path
) -> None:
    arrived: list[float] = []
    runner = RedisScopeRunner(
        AnalysisRepository(app_settings.storage),
        AnalysisSettings(
            redisscope_binary=_script(tmp_path, "talkative", _TALKATIVE_ANALYZER),
            timeout_seconds=60,
            console_log_name=app_settings.analysis.console_log_name,
        ),
        app_settings.storage,
        on_line=lambda _, __: arrived.append(time.monotonic()),
    )

    started = time.monotonic()
    runner.analyze(package, AnalysisOptions())
    finished = time.monotonic()

    assert arrived[0] - started < (finished - started) / 2


def test_an_analyzer_that_never_finishes_times_out(
    app_settings: AppSettings, package: StoredPackage, tmp_path: Path
) -> None:
    runner = RedisScopeRunner(
        AnalysisRepository(app_settings.storage),
        AnalysisSettings(
            redisscope_binary=_script(tmp_path, "stuck", _STUCK_ANALYZER),
            timeout_seconds=1,
            console_log_name=app_settings.analysis.console_log_name,
        ),
        app_settings.storage,
    )

    with pytest.raises(AnalysisTimeoutError):
        runner.analyze(package, AnalysisOptions())

    assert AnalysisRepository(app_settings.storage).list()[0].metadata.status is (
        AnalysisStatus.TIMED_OUT
    )


_PROGRESS_ANALYZER = """#!/bin/sh
printf 'reading the package'
printf '\\r 10%% read'
printf '\\r 60%% read'
printf '\\r100%% read\\n'
printf '\\033[32mall done\\033[0m\\n'
mkdir -p redisscope_html
"""


def test_a_progress_line_arrives_as_it_is_rewritten(
    app_settings: AppSettings, package: StoredPackage, tmp_path: Path
) -> None:
    updates: list[tuple[str, bool]] = []
    runner = RedisScopeRunner(
        AnalysisRepository(app_settings.storage),
        AnalysisSettings(
            redisscope_binary=_script(tmp_path, "progress", _PROGRESS_ANALYZER),
            timeout_seconds=60,
            console_log_name=app_settings.analysis.console_log_name,
        ),
        app_settings.storage,
        on_line=lambda text, overwrite: updates.append((text, overwrite)),
    )

    runner.analyze(package, AnalysisOptions())

    assert updates[0] == ("reading the package", False)
    assert (" 10% read", True) in updates
    assert ("100% read", True) in updates


def test_the_colour_codes_never_reach_the_log(
    app_settings: AppSettings, package: StoredPackage, tmp_path: Path
) -> None:
    lines: list[str] = []
    runner = RedisScopeRunner(
        AnalysisRepository(app_settings.storage),
        AnalysisSettings(
            redisscope_binary=_script(tmp_path, "coloured", _PROGRESS_ANALYZER),
            timeout_seconds=60,
            console_log_name=app_settings.analysis.console_log_name,
        ),
        app_settings.storage,
        on_line=lambda text, _: lines.append(text),
    )

    runner.analyze(package, AnalysisOptions())

    assert "all done" in lines
    assert all("\x1b" not in line for line in lines)


def test_the_saved_run_log_keeps_the_raw_output(
    app_settings: AppSettings, package: StoredPackage, tmp_path: Path
) -> None:
    runner = RedisScopeRunner(
        AnalysisRepository(app_settings.storage),
        AnalysisSettings(
            redisscope_binary=_script(tmp_path, "raw", _PROGRESS_ANALYZER),
            timeout_seconds=60,
            console_log_name=app_settings.analysis.console_log_name,
        ),
        app_settings.storage,
    )

    analysis = runner.analyze(package, AnalysisOptions())

    log_path = analysis.directory / app_settings.analysis.console_log_name
    with log_path.open(encoding="utf-8", newline="") as stream:
        saved = stream.read()
    assert "\r 10% read" in saved
    assert "\x1b[32mall done" in saved
