from datetime import UTC, datetime, timedelta

import pytest

from rs_collector.analysis.models import AnalysisMetadata
from rs_collector.analysis.options import AnalysisOptions
from rs_collector.analysis.repository import AnalysisRepository
from rs_collector.exceptions.storage import ArtifactNotFoundError
from rs_collector.packages.models import PackageMetadata
from rs_collector.packages.repository import PackageRepository
from rs_collector.retention.cleaner import RetentionCleaner
from rs_collector.retention.pin import PinService
from rs_collector.retention.policy import RetentionPolicy
from rs_collector.settings.models import AppSettings

pytestmark = pytest.mark.unit

_NOW = datetime(2026, 9, 19, 12, 0, tzinfo=UTC)


@pytest.fixture
def packages(app_settings: AppSettings) -> PackageRepository:
    return PackageRepository(app_settings.storage)


@pytest.fixture
def analyses(app_settings: AppSettings) -> AnalysisRepository:
    return AnalysisRepository(app_settings.storage)


@pytest.fixture
def cleaner(
    packages: PackageRepository, analyses: AnalysisRepository, app_settings: AppSettings
) -> RetentionCleaner:
    return RetentionCleaner(
        packages, analyses, RetentionPolicy(max_age_days=app_settings.retention.max_age_days)
    )


def _package(name: str, age_days: int, pinned: bool = False) -> PackageMetadata:
    return PackageMetadata(
        name=name,
        cluster_fqdn="c1.example.com",
        collected_from="n1.c1.example.com",
        collected_at=_NOW - timedelta(days=age_days),
        original_file_name="debuginfo.tar.gz",
        size_bytes=10,
        sha256="a" * 64,
        pinned=pinned,
    )


def _analysis(name: str, age_days: int, pinned: bool = False) -> AnalysisMetadata:
    return AnalysisMetadata(
        name=name,
        package_name="c1__old",
        cluster_fqdn="c1.example.com",
        options=AnalysisOptions(),
        command=("redisscope",),
        analyzed_at=_NOW - timedelta(days=age_days),
        pinned=pinned,
    )


def test_a_package_older_than_a_week_expires(packages: PackageRepository) -> None:
    policy = RetentionPolicy(max_age_days=7)

    assert policy.package_expired(packages.save(_package("old", age_days=8)), _NOW)


def test_a_package_from_this_week_stays(packages: PackageRepository) -> None:
    policy = RetentionPolicy(max_age_days=7)

    assert not policy.package_expired(packages.save(_package("fresh", age_days=3)), _NOW)


def test_a_pinned_package_never_expires(packages: PackageRepository) -> None:
    policy = RetentionPolicy(max_age_days=7)

    assert not policy.package_expired(
        packages.save(_package("kept", age_days=90, pinned=True)), _NOW
    )


def test_cleanup_removes_an_expired_package(
    cleaner: RetentionCleaner, packages: PackageRepository
) -> None:
    packages.save(_package("old", age_days=8))

    cleaner.clean(now=_NOW)

    assert packages.list() == ()


def test_cleanup_keeps_a_recent_package(
    cleaner: RetentionCleaner, packages: PackageRepository
) -> None:
    packages.save(_package("fresh", age_days=1))

    cleaner.clean(now=_NOW)

    assert len(packages.list()) == 1


def test_cleanup_removes_an_expired_analysis(
    cleaner: RetentionCleaner, analyses: AnalysisRepository
) -> None:
    analyses.create(_analysis("old", age_days=8))

    cleaner.clean(now=_NOW)

    assert analyses.list() == ()


def test_cleanup_keeps_a_pinned_analysis(
    cleaner: RetentionCleaner, analyses: AnalysisRepository
) -> None:
    analyses.create(_analysis("kept", age_days=30, pinned=True))

    cleaner.clean(now=_NOW)

    assert len(analyses.list()) == 1


def test_a_dry_run_removes_nothing(cleaner: RetentionCleaner, packages: PackageRepository) -> None:
    packages.save(_package("old", age_days=8))

    report = cleaner.clean(dry_run=True, now=_NOW)

    assert report.removed_packages == ("old",) and len(packages.list()) == 1


def test_pinning_a_package_protects_it(
    packages: PackageRepository, analyses: AnalysisRepository
) -> None:
    packages.save(_package("old", age_days=8))

    PinService(packages, analyses).pin("old")

    assert packages.get("old").metadata.pinned


def test_pinning_an_analysis_protects_it(
    packages: PackageRepository, analyses: AnalysisRepository
) -> None:
    analyses.create(_analysis("old", age_days=8))

    PinService(packages, analyses).pin("old")

    assert analyses.get("old").metadata.pinned


def test_unpinning_lets_an_item_expire_again(
    packages: PackageRepository, analyses: AnalysisRepository
) -> None:
    packages.save(_package("kept", age_days=8, pinned=True))

    PinService(packages, analyses).unpin("kept")

    assert not packages.get("kept").metadata.pinned


def test_pinning_an_unknown_name_is_reported(
    packages: PackageRepository, analyses: AnalysisRepository
) -> None:
    with pytest.raises(ArtifactNotFoundError):
        PinService(packages, analyses).pin("missing")
