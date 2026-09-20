import pytest

from rs_collector.analysis.command import RedisScopeCommandBuilder
from rs_collector.analysis.namer import AnalysisNamer
from rs_collector.analysis.options import AnalysisDepth, AnalysisOptions

pytestmark = pytest.mark.unit

_BINARY = "/opt/redisscope/redisscope"
_ARCHIVE = "/data/redisscope/packages/c1__now/support_package.tar.gz"


def test_default_options_add_no_flags() -> None:
    assert AnalysisOptions().flags == ()


@pytest.mark.parametrize(
    ("depth", "expected"),
    [
        (AnalysisDepth.QUICK, ("--skiplogs",)),
        (AnalysisDepth.DEFAULT, ()),
        (AnalysisDepth.FULL, ("--force-full",)),
        (AnalysisDepth.MAX, ("--force-full", "--count-pattern-occurrences")),
    ],
)
def test_depth_maps_to_its_flags(depth: AnalysisDepth, expected: tuple[str, ...]) -> None:
    assert AnalysisOptions(depth=depth).flags == expected


def test_a_database_becomes_a_bdb_flag() -> None:
    assert AnalysisOptions(bdb_id=5).flags == ("--bdb", "5")


def test_masking_becomes_a_mask_flag() -> None:
    assert AnalysisOptions(mask=True).flags == ("--mask",)


def test_flags_keep_the_documented_order() -> None:
    options = AnalysisOptions(bdb_id=5, depth=AnalysisDepth.MAX, mask=True)

    assert options.flags == (
        "--bdb",
        "5",
        "--force-full",
        "--count-pattern-occurrences",
        "--mask",
    )


def test_default_options_are_named_default() -> None:
    assert AnalysisOptions().slug() == "default"


def test_slug_describes_every_chosen_option() -> None:
    options = AnalysisOptions(bdb_id=5, depth=AnalysisDepth.MAX, mask=True)

    assert options.slug() == "bdb-5__max__masked"


def test_command_starts_with_the_binary_and_the_package() -> None:
    from pathlib import Path

    command = RedisScopeCommandBuilder(Path(_BINARY)).build(Path(_ARCHIVE), AnalysisOptions())

    assert command == (_BINARY, "--sp", _ARCHIVE)


def test_command_appends_the_option_flags() -> None:
    from pathlib import Path

    command = RedisScopeCommandBuilder(Path(_BINARY)).build(
        Path(_ARCHIVE), AnalysisOptions(bdb_id=3)
    )

    assert command[-2:] == ("--bdb", "3")


def test_namer_uses_the_package_name_and_the_slug() -> None:
    name = AnalysisNamer().name_for("c1__2026-09-19_14-30-05", AnalysisOptions(), ())

    assert name == "c1__2026-09-19_14-30-05__default"


def test_namer_adds_a_suffix_for_a_repeated_analysis() -> None:
    taken = ("c1__now__default",)

    assert AnalysisNamer().name_for("c1__now", AnalysisOptions(), taken) == "c1__now__default__2"


def test_namer_keeps_counting_repeated_analyses() -> None:
    taken = ("c1__now__default", "c1__now__default__2")

    assert AnalysisNamer().name_for("c1__now", AnalysisOptions(), taken) == "c1__now__default__3"
