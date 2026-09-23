import os
from datetime import UTC, datetime, timedelta

import pytest
from tests.fakes import FakeCrontab

from rs_collector.analysis.repository import AnalysisRepository
from rs_collector.background.crontab import CrontabInstaller
from rs_collector.background.pid_file import PidFile
from rs_collector.packages.models import PackageMetadata
from rs_collector.packages.repository import PackageRepository
from rs_collector.retention.cleaner import CleanupReport
from rs_collector.retention.history import CleanupHistory
from rs_collector.settings.models import AppSettings
from rs_collector.status.service import StatusService

pytestmark = pytest.mark.unit


def _metadata(name: str, pinned: bool = False) -> PackageMetadata:
    return PackageMetadata(
        name=name,
        cluster_fqdn="c1.example.com",
        collected_from="n1.c1.example.com",
        collected_at=datetime.now(UTC) - timedelta(hours=2),
        original_file_name="debuginfo.tar.gz",
        size_bytes=2_097_152,
        sha256="a" * 64,
        pinned=pinned,
    )


@pytest.fixture
def crontab() -> FakeCrontab:
    return FakeCrontab()


@pytest.fixture
def service(app_settings: AppSettings, crontab: FakeCrontab) -> StatusService:
    app_settings.storage.data_root.mkdir(parents=True, exist_ok=True)
    return StatusService(
        app_settings,
        PidFile(app_settings.storage.locks_dir / app_settings.background.pid_file_name),
        CrontabInstaller(crontab, app_settings.background.crontab_marker),
        CleanupHistory(app_settings.storage),
        PackageRepository(app_settings.storage),
        AnalysisRepository(app_settings.storage),
    )


def test_a_stopped_server_is_reported(service: StatusService) -> None:
    assert service.collect().server.is_running is False


def test_a_running_server_is_reported(service: StatusService, app_settings: AppSettings) -> None:
    PidFile(app_settings.storage.locks_dir / app_settings.background.pid_file_name).write(
        os.getpid()
    )

    assert service.collect().server.pid == os.getpid()


def test_the_reboot_schedule_is_reported(service: StatusService, crontab: FakeCrontab) -> None:
    crontab.content = "@reboot rsc start # rsc\n"

    assert service.collect().schedule.starts_after_reboot is True


def test_a_missing_reboot_schedule_is_reported(service: StatusService) -> None:
    assert service.collect().schedule.starts_after_reboot is False


def test_the_last_cleanup_is_reported(service: StatusService, app_settings: AppSettings) -> None:
    moment = datetime(2026, 9, 23, 3, 30, tzinfo=UTC)
    CleanupHistory(app_settings.storage).record(
        CleanupReport(removed_packages=("old",)), finished_at=moment
    )

    schedule = service.collect().schedule
    assert schedule.cleanup_last_run == moment
    assert schedule.removed_last_run == 1


def test_the_free_disk_space_is_reported(service: StatusService) -> None:
    assert service.collect().storage.free_bytes > 0


def test_the_stored_packages_are_counted(service: StatusService, app_settings: AppSettings) -> None:
    repository = PackageRepository(app_settings.storage)
    repository.save(_metadata("first"))
    repository.save(_metadata("second", pinned=True))

    storage = service.collect().storage
    assert storage.packages == 2
    assert storage.packages_bytes == 4_194_304
    assert storage.pinned == 1
