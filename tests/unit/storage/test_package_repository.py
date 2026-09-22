from datetime import UTC, datetime

import pytest

from rs_collector.exceptions.storage import MetadataError, PackageNotFoundError
from rs_collector.packages.models import PackageMetadata
from rs_collector.packages.namer import PackageNamer
from rs_collector.packages.repository import PackageRepository
from rs_collector.settings.models import AppSettings

pytestmark = pytest.mark.unit

_COLLECTED_AT = datetime(2026, 9, 19, 14, 30, 5, tzinfo=UTC)
_DIGEST = "a" * 64


@pytest.fixture
def repository(app_settings: AppSettings) -> PackageRepository:
    return PackageRepository(app_settings.storage)


def _metadata(name: str, collected_at: datetime = _COLLECTED_AT) -> PackageMetadata:
    return PackageMetadata(
        name=name,
        cluster_fqdn="c1.example.com",
        environment="production",
        collected_from="n1.c1.example.com",
        collected_at=collected_at,
        original_file_name="debuginfo.tar.gz",
        size_bytes=1024,
        sha256=_DIGEST,
    )


def test_namer_joins_the_cluster_and_the_timestamp() -> None:
    assert (
        PackageNamer().name_for("c1.example.com", _COLLECTED_AT)
        == "c1.example.com__2026-09-19_14-30-05"
    )


def test_create_slot_creates_the_package_directory(repository: PackageRepository) -> None:
    slot = repository.create_slot("c1.example.com", _COLLECTED_AT)

    assert slot.directory.is_dir()


def test_create_slot_points_at_the_archive_file(repository: PackageRepository) -> None:
    slot = repository.create_slot("c1.example.com", _COLLECTED_AT)

    assert slot.archive_path.name == "support_package.tar.gz"


def test_save_writes_the_metadata_file(repository: PackageRepository) -> None:
    stored = repository.save(_metadata("c1.example.com__2026-09-19_14-30-05"))

    assert (stored.directory / "package.json").is_file()


def test_get_reads_a_stored_package(repository: PackageRepository) -> None:
    repository.save(_metadata("c1.example.com__2026-09-19_14-30-05"))

    stored = repository.get("c1.example.com__2026-09-19_14-30-05")

    assert stored.metadata.cluster_fqdn == "c1.example.com"


def test_get_rejects_an_unknown_package(repository: PackageRepository) -> None:
    with pytest.raises(PackageNotFoundError):
        repository.get("missing")


def test_get_rejects_broken_metadata(repository: PackageRepository) -> None:
    stored = repository.save(_metadata("c1.example.com__2026-09-19_14-30-05"))
    (stored.directory / "package.json").write_text("{", encoding="utf-8")

    with pytest.raises(MetadataError):
        repository.get(stored.name)


def test_list_returns_the_newest_package_first(repository: PackageRepository) -> None:
    repository.save(_metadata("old", datetime(2026, 9, 1, tzinfo=UTC)))
    repository.save(_metadata("new", datetime(2026, 9, 19, tzinfo=UTC)))

    assert [package.name for package in repository.list()] == ["new", "old"]


def test_list_is_empty_without_a_packages_directory(repository: PackageRepository) -> None:
    assert repository.list() == ()


def test_delete_removes_the_package_directory(repository: PackageRepository) -> None:
    stored = repository.save(_metadata("c1.example.com__2026-09-19_14-30-05"))

    repository.delete(stored.name)

    assert not stored.directory.exists()


def test_list_skips_a_package_with_broken_metadata(repository: PackageRepository) -> None:
    repository.save(_metadata("good"))
    broken = repository.save(_metadata("broken"))
    (broken.directory / "package.json").write_text("{not json", encoding="utf-8")

    assert [package.name for package in repository.list()] == ["good"]
