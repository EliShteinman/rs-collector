import pytest

from rs_collector.background.program import RscProgram
from rs_collector.runtime.bundle import BundleLocator

pytestmark = pytest.mark.unit


class _Locator(BundleLocator):
    def __init__(self, frozen: bool) -> None:
        super().__init__()
        self._frozen = frozen

    def is_frozen(self) -> bool:
        return self._frozen


def test_the_packaged_executable_runs_itself() -> None:
    program = RscProgram(_Locator(frozen=True), executable="/opt/rsc/bin/rsc")

    assert program.argv("serve") == ("/opt/rsc/bin/rsc", "serve")


def test_a_source_checkout_runs_the_cli_module() -> None:
    program = RscProgram(_Locator(frozen=False), executable="/usr/bin/python3")

    assert program.argv("serve") == ("/usr/bin/python3", "-m", "rs_collector.cli.app", "serve")
