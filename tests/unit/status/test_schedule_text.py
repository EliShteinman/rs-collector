import pytest

from rs_collector.status.schedule_text import spoken

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("schedule", "expected"),
    [
        ("30 3 * * *", "daily at 03:30"),
        ("0 0 * * *", "daily at 00:00"),
        ("*/15 * * * *", "*/15 * * * *"),
        ("30 3 * * 1", "30 3 * * 1"),
    ],
)
def test_a_daily_schedule_is_spelled_out(schedule: str, expected: str) -> None:
    assert spoken(schedule) == expected
