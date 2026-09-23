import gzip
from pathlib import Path

import pytest

from rs_collector.exceptions.storage import ArtifactNotFoundError
from rs_collector.web.files.reader import FileReader

pytestmark = pytest.mark.unit

_LINES = "\n".join(f"line {number}" for number in range(200)).encode("utf-8")


@pytest.fixture
def reader() -> FileReader:
    return FileReader(max_inline_bytes=1_048_576)


def test_a_log_is_shown_as_text(reader: FileReader, tmp_path: Path) -> None:
    log = tmp_path / "redisscope_current.log"
    log.write_bytes(_LINES)

    body, content_type = reader.read(log)

    assert body == _LINES
    assert content_type == "text/plain; charset=utf-8"


def test_a_rotated_log_is_unpacked_for_reading(reader: FileReader, tmp_path: Path) -> None:
    archived = tmp_path / "redis-server.log.1.gz"
    archived.write_bytes(gzip.compress(_LINES))

    body, content_type = reader.read(archived)

    assert body == _LINES
    assert content_type == "text/plain; charset=utf-8"


def test_a_rotated_log_can_be_downloaded_as_it_is(reader: FileReader, tmp_path: Path) -> None:
    archived = tmp_path / "redis-server.log.1.gz"
    packed = gzip.compress(_LINES)
    archived.write_bytes(packed)

    body, content_type = reader.read(archived, raw=True)

    assert body == packed
    assert content_type == "application/gzip"


def test_a_report_keeps_its_html_type(reader: FileReader, tmp_path: Path) -> None:
    report = tmp_path / "index.html"
    report.write_text("<html></html>", encoding="utf-8")

    assert reader.read(report)[1] == "text/html; charset=utf-8"


def test_an_archive_of_something_else_is_downloaded(reader: FileReader, tmp_path: Path) -> None:
    archive = tmp_path / "support_package.tar.gz"
    archive.write_bytes(gzip.compress(b"binary"))

    assert reader.read(archive)[1] == "application/x-tar"


def test_a_huge_log_shows_its_tail(tmp_path: Path) -> None:
    log = tmp_path / "redisscope_current.log"
    log.write_bytes(_LINES)

    body, _ = FileReader(max_inline_bytes=50).read(log)

    assert body.endswith(_LINES[-50:])
    assert b"showing the last 50 bytes" in body


def test_a_broken_archive_is_reported(reader: FileReader, tmp_path: Path) -> None:
    broken = tmp_path / "redis-server.log.1.gz"
    broken.write_bytes(b"not gzip at all")

    with pytest.raises(ArtifactNotFoundError):
        reader.read(broken)


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("style.css", "text/css; charset=utf-8"),
        ("app.js", "text/javascript; charset=utf-8"),
        ("index.html", "text/html; charset=utf-8"),
        ("redisscope_current.log", "text/plain; charset=utf-8"),
        ("chart.svg", "image/svg+xml"),
        ("logo.png", "image/png"),
    ],
)
def test_the_report_assets_keep_their_own_type(
    reader: FileReader, tmp_path: Path, name: str, expected: str
) -> None:
    asset = tmp_path / name
    asset.write_text("body { color: red }", encoding="utf-8")

    assert reader.read(asset)[1] == expected
