import pytest

from rs_collector.web.views.size_text import size

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("byte_count", "expected"),
    [
        (0, "0 B"),
        (512, "512 B"),
        (2048, "2.0 KB"),
        (4036, "3.9 KB"),
        (1_572_864, "1.5 MB"),
        (1_572_864_000, "1.5 GB"),
        (2_199_023_255_552, "2.0 TB"),
    ],
)
def test_a_size_is_shown_in_its_natural_unit(byte_count: int, expected: str) -> None:
    assert size(byte_count) == expected
