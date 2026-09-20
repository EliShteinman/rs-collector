import pytest

from rs_collector.exceptions import (
    AnalysisFailedError,
    ClusterUnreachableError,
    CollectionAlreadyRunningError,
    ConfigFileNotFoundError,
    ConnectionStringError,
    PackageNotFoundError,
    RsCollectorError,
)

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    "error_type",
    [
        AnalysisFailedError,
        ClusterUnreachableError,
        CollectionAlreadyRunningError,
        ConfigFileNotFoundError,
        ConnectionStringError,
        PackageNotFoundError,
    ],
)
def test_every_error_derives_from_the_application_base(error_type: type[Exception]) -> None:
    assert issubclass(error_type, RsCollectorError)


def test_application_base_derives_from_exception() -> None:
    assert issubclass(RsCollectorError, Exception)
