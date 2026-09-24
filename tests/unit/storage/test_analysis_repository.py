from datetime import UTC, datetime

import pytest

from rs_collector.analysis.models import AnalysisMetadata, AnalysisStatus
from rs_collector.analysis.options import AnalysisOptions
from rs_collector.analysis.repository import AnalysisRepository
from rs_collector.exceptions.storage import AnalysisNotFoundError
from rs_collector.settings.models import AppSettings

pytestmark = pytest.mark.unit


@pytest.fixture
def repository(app_settings: AppSettings) -> AnalysisRepository:
    return AnalysisRepository(app_settings.storage)


def _metadata(name: str) -> AnalysisMetadata:
    return AnalysisMetadata(
        name=name,
        package_name="c1.example.com__2026-09-19_14-30-05",
        cluster_fqdn="c1.example.com",
        options=AnalysisOptions(),
        command=("redisscope", "--sp", "package.tar.gz"),
        analyzed_at=datetime(2026, 9, 19, 15, 0, 0, tzinfo=UTC),
        status=AnalysisStatus.SUCCEEDED,
    )


def test_a_saved_analysis_is_returned(repository: AnalysisRepository) -> None:
    repository.create(_metadata("run-1"))

    assert repository.get("run-1").metadata.cluster_fqdn == "c1.example.com"


def test_an_unknown_name_is_not_found(repository: AnalysisRepository) -> None:
    with pytest.raises(AnalysisNotFoundError):
        repository.get("never-ran")


def test_a_directory_without_metadata_is_not_an_analysis(
    repository: AnalysisRepository, app_settings: AppSettings
) -> None:
    (app_settings.storage.analyses_dir / "half-written").mkdir(parents=True)

    with pytest.raises(AnalysisNotFoundError):
        repository.get("half-written")
