import pytest

from rs_collector.console.choice import ChoicePrompt
from rs_collector.console.io import ScriptedConsole
from rs_collector.exceptions.selection import EmptyInventoryError, SelectionAbortedError
from rs_collector.inventory.models import Inventory
from rs_collector.selection.interactive import InteractiveClusterSelector

pytestmark = pytest.mark.unit


class StaticInventoryRepository:
    def __init__(self, inventory: Inventory) -> None:
        self._inventory = inventory

    def load(self) -> Inventory:
        return self._inventory


@pytest.fixture
def inventory() -> Inventory:
    return Inventory.model_validate(
        {
            "environments": [
                {
                    "name": "production",
                    "clusters": [{"fqdn": "c1.example.com"}, {"fqdn": "c2.example.com"}],
                },
                {"name": "staging", "clusters": [{"fqdn": "c3.example.com"}]},
            ]
        }
    )


def _selector(inventory: Inventory, answers: list[str]) -> InteractiveClusterSelector:
    console = ScriptedConsole(answers)
    return InteractiveClusterSelector(StaticInventoryRepository(inventory), ChoicePrompt(console))


def test_select_returns_the_chosen_cluster(inventory: Inventory) -> None:
    assert _selector(inventory, ["1", "2"]).select().name == "c2.example.com"


def test_select_skips_the_cluster_question_for_a_single_cluster(inventory: Inventory) -> None:
    assert _selector(inventory, ["2"]).select().name == "c3.example.com"


def test_select_asks_again_after_an_invalid_answer(inventory: Inventory) -> None:
    assert _selector(inventory, ["9", "x", "1", "1"]).select().name == "c1.example.com"


def test_select_rejects_an_empty_inventory() -> None:
    with pytest.raises(EmptyInventoryError):
        _selector(Inventory(), []).select()


def test_select_stops_when_the_input_ends(inventory: Inventory) -> None:
    with pytest.raises(SelectionAbortedError):
        _selector(inventory, []).select()
