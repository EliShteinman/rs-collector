import pytest

from rs_collector.collection.output_parser import DebugInfoOutputParser
from rs_collector.exceptions.remote import DebugInfoOutputError

pytestmark = pytest.mark.unit


@pytest.fixture
def parser() -> DebugInfoOutputParser:
    return DebugInfoOutputParser()


def test_package_path_is_read_from_the_saved_line(parser: DebugInfoOutputParser) -> None:
    output = "Collecting...\nFile /tmp/debuginfo.mup.cluster1.tar.gz is saved.\n"

    assert parser.package_path(output) == "/tmp/debuginfo.mup.cluster1.tar.gz"


def test_package_path_ignores_the_case_of_the_saved_line(parser: DebugInfoOutputParser) -> None:
    output = "file /tmp/debuginfo.tar.gz IS SAVED"

    assert parser.package_path(output) == "/tmp/debuginfo.tar.gz"


def test_package_path_falls_back_to_the_archive_path(parser: DebugInfoOutputParser) -> None:
    output = "Storing the package at /tmp/debuginfo.mup.cluster1.tar.gz\n"

    assert parser.package_path(output) == "/tmp/debuginfo.mup.cluster1.tar.gz"


def test_package_path_takes_the_last_reported_file(parser: DebugInfoOutputParser) -> None:
    output = "File /tmp/old.tar.gz is saved\nFile /tmp/new.tar.gz is saved\n"

    assert parser.package_path(output) == "/tmp/new.tar.gz"


@pytest.mark.parametrize("output", ["", "ERROR: node is down", "nothing useful here"])
def test_package_path_rejects_output_without_a_package(
    parser: DebugInfoOutputParser, output: str
) -> None:
    with pytest.raises(DebugInfoOutputError):
        parser.package_path(output)
