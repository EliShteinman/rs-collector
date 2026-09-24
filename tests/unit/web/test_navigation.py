import pytest

from rs_collector.web.navigation import Navigation, Tool

pytestmark = pytest.mark.unit

_CONSOLE = Tool(name="Collect & analyze", path="/", summary="the console")
_FILES = Tool(name="Stored files", path="/analyses/", summary="every file")


def _navigation(path: str) -> Navigation:
    return Navigation(tools=(_CONSOLE, _FILES)).here(path)


def test_the_console_is_current_on_the_home_page() -> None:
    assert _navigation("/").is_here(_CONSOLE) is True


def test_the_console_is_not_current_elsewhere() -> None:
    assert _navigation("/analyses/run-1/").is_here(_CONSOLE) is False


def test_a_tool_is_current_on_its_own_page() -> None:
    assert _navigation("/analyses/").is_here(_FILES) is True


def test_a_tool_is_current_deeper_inside_it() -> None:
    assert (
        _navigation("/analyses/run-1/redisscope_sp/node_1/logs/redis_3.log").is_here(_FILES) is True
    )


def test_a_tool_is_not_current_on_another_path() -> None:
    assert _navigation("/jobs/abc").is_here(_FILES) is False


def test_navigation_without_a_page_marks_nothing() -> None:
    plain = Navigation(tools=(_CONSOLE, _FILES))

    assert plain.is_here(_CONSOLE) is False


def test_the_tools_are_kept_when_the_page_changes() -> None:
    assert _navigation("/jobs/abc").tools == (_CONSOLE, _FILES)
