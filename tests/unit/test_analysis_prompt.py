import pytest

from rs_collector.analysis.options import AnalysisDepth
from rs_collector.analysis.prompt import AnalysisOptionsPrompt
from rs_collector.console.io import ScriptedConsole

pytestmark = pytest.mark.unit


def _ask(answers: list[str]):
    return AnalysisOptionsPrompt(ScriptedConsole(answers)).ask()


def test_pressing_enter_three_times_gives_the_default_options() -> None:
    assert _ask(["", "", ""]).flags == ()


def test_a_database_number_is_kept() -> None:
    assert _ask(["7", "", ""]).bdb_id == 7


def test_the_depth_question_accepts_a_number() -> None:
    assert _ask(["", "4", ""]).depth is AnalysisDepth.MAX


def test_the_mask_question_accepts_yes() -> None:
    assert _ask(["", "", "2"]).mask is True


def test_an_invalid_database_answer_is_asked_again() -> None:
    assert _ask(["abc", "0", "3", "", ""]).bdb_id == 3


def test_an_invalid_depth_answer_is_asked_again() -> None:
    assert _ask(["", "9", "1", ""]).depth is AnalysisDepth.QUICK
