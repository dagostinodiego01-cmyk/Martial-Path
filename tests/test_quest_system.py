"""Tests for the data-driven quest/journal system."""
from game.models.item import Item
from game.models.player import Player
from game.systems.effect_system import EffectSystem
from game.systems.inventory_system import InventorySystem
from game.systems.quest_system import QuestSystem

QUESTS = [
    {
        "id": "slayer",
        "title": "Slayer",
        "auto_start": True,
        "objectives": [{"type": "defeat", "target": "any", "count": 2, "text": "Defeat 2"}],
        "rewards": {"exp": 10, "gold": 5, "items": {"healing_pill": 1}},
    },
    {
        "id": "locked_quest",
        "title": "Locked",
        "objectives": [{"type": "defeat", "target": "any", "count": 1, "text": "Defeat 1"}],
        "rewards": {},
    },
]


def _inventory():
    items = {
        "healing_pill": Item.from_dict(
            {
                "id": "healing_pill",
                "name": "Healing Pill",
                "type": "consumable",
                "effect": "heal",
                "magnitude": 40,
                "description": "",
            }
        )
    }
    return InventorySystem(items, EffectSystem())


def test_auto_start_quests_are_active_others_locked():
    quests = QuestSystem(QUESTS)
    snap = {q["id"]: q for q in quests.snapshot()}
    assert snap["slayer"]["status"] == "active"
    assert snap["locked_quest"]["status"] == "locked"


def test_notify_advances_and_completes_with_rewards():
    quests = QuestSystem(QUESTS)
    player = Player(name="Tester")
    inventory = _inventory()

    assert quests.notify("defeat", player, inventory) == []  # 1/2

    completed = quests.notify("defeat", player, inventory)  # 2/2
    assert len(completed) == 1
    assert completed[0]["id"] == "slayer"
    assert player.exp == 10
    assert player.gold == 5
    assert player.inventory.get("healing_pill", 0) == 1


def test_completed_quest_ignores_further_events():
    quests = QuestSystem(QUESTS)
    player = Player(name="Tester")
    inventory = _inventory()
    quests.notify("defeat", player, inventory)
    quests.notify("defeat", player, inventory)  # completes
    exp_after = player.exp
    quests.notify("defeat", player, inventory)  # no further effect
    assert player.exp == exp_after


def test_target_filtering_matches_specific_ids():
    quests = QuestSystem(
        [
            {
                "id": "boss",
                "title": "Boss",
                "auto_start": True,
                "objectives": [{"type": "defeat", "target": "corpse_demon", "count": 1, "text": "x"}],
                "rewards": {},
            }
        ]
    )
    player = Player(name="Tester")
    inventory = _inventory()
    assert quests.notify("defeat", player, inventory, target="iron_wolf") == []
    assert len(quests.notify("defeat", player, inventory, target="corpse_demon")) == 1
