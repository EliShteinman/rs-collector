from datetime import UTC, datetime
from pathlib import Path

import pytest

from rs_collector.analysis.models import AnalysisMetadata, StoredAnalysis
from rs_collector.analysis.options import AnalysisOptions
from rs_collector.analysis.outputs import AnalysisOutputs

pytestmark = pytest.mark.unit


def _analysis(directory: Path, mask: bool = False) -> StoredAnalysis:
    return StoredAnalysis(
        metadata=AnalysisMetadata(
            name=directory.name,
            package_name="c1.example.com__2026-09-23_07-38-00",
            cluster_fqdn="c1.example.com",
            options=AnalysisOptions(mask=mask),
            command=("redisscope", "--sp", "package.tar.gz"),
            analyzed_at=datetime.now(UTC),
        ),
        directory=directory,
    )


@pytest.fixture
def directory(tmp_path: Path) -> Path:
    built = tmp_path / "analysis"
    built.mkdir()
    return built


def _page(directory: Path, relative: str) -> Path:
    page = directory / relative
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text("<html></html>", encoding="utf-8")
    return page


def test_no_report_before_the_analyzer_wrote_one(directory: Path) -> None:
    assert AnalysisOutputs(_analysis(directory)).report() is None


def test_the_index_of_the_html_directory_is_the_report(directory: Path) -> None:
    expected = _page(directory, "redisscope_html/index.html")

    assert AnalysisOutputs(_analysis(directory)).report() == expected


def test_any_page_of_the_html_directory_will_do(directory: Path) -> None:
    expected = _page(directory, "redisscope_html/cluster_overview.html")

    assert AnalysisOutputs(_analysis(directory)).report() == expected


def test_a_masked_analysis_opens_the_masked_report(directory: Path) -> None:
    _page(directory, "redisscope_html/index.html")
    expected = _page(directory, "redisscope_html_mask/index.html")

    assert AnalysisOutputs(_analysis(directory, mask=True)).report() == expected


def test_an_unmasked_analysis_opens_the_plain_report(directory: Path) -> None:
    expected = _page(directory, "redisscope_html/index.html")
    _page(directory, "redisscope_html_mask/index.html")

    assert AnalysisOutputs(_analysis(directory)).report() == expected


def test_a_healthcheck_page_is_used_when_there_is_no_html_directory(directory: Path) -> None:
    expected = _page(directory, "redisscope_healthcheck_report.html")

    assert AnalysisOutputs(_analysis(directory)).report() == expected


def test_the_raw_logs_directory_is_found(directory: Path) -> None:
    (directory / "redisscope_sp").mkdir()

    assert AnalysisOutputs(_analysis(directory)).raw_logs() == directory / "redisscope_sp"


def test_no_raw_logs_before_the_package_is_extracted(directory: Path) -> None:
    assert AnalysisOutputs(_analysis(directory)).raw_logs() is None


def test_the_run_log_of_the_analyzer_is_found(directory: Path) -> None:
    (directory / "analysis_console.log").write_text("started\n", encoding="utf-8")

    assert AnalysisOutputs(_analysis(directory)).analyzer_log() == (
        directory / "analysis_console.log"
    )


def test_the_analyzer_own_log_is_used_when_there_is_no_console_log(directory: Path) -> None:
    (directory / "redisscope_current.log").write_text("analyzing\n", encoding="utf-8")

    assert AnalysisOutputs(_analysis(directory)).analyzer_log() == (
        directory / "redisscope_current.log"
    )


def test_no_run_log_before_the_analyzer_started(directory: Path) -> None:
    assert AnalysisOutputs(_analysis(directory)).analyzer_log() is None
