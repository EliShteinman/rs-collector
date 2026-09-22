import pytest

from rs_collector.exceptions.privileges import RunningAsRootError
from rs_collector.runtime.privileges import PrivilegeGuard

pytestmark = pytest.mark.unit


def test_a_regular_user_is_accepted() -> None:
    PrivilegeGuard(effective_user_id=lambda: 1000).refuse_root()


def test_root_is_refused() -> None:
    with pytest.raises(RunningAsRootError):
        PrivilegeGuard(effective_user_id=lambda: 0).refuse_root()
