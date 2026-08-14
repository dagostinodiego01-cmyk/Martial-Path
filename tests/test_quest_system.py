"""Tests for the data-driven quest/journal system."""
from game.models.item import Item
from game.models.player import Player
from game.models.skill import Skill
from game.systems.effect_system import EffectSystem
from game.systems.inventory_system import InventorySystem
from game.systems.quest_system import QuestSystem
from game.systems.skill_system import SkillSystem

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
        ),
        "spirit_palm_manual": Item.from_dict(
            {
                "id": "spirit_palm_manual",
                "name": "Spirit-Severing Palm Manual",
                "type": "technique",
                "effect": "learn_skill",
                "magnitude": 0,
                "skill_id": "spirit_palm",
                "description": "",
            }
        ),
    }
    return InventorySystem(items, EffectSystem())


def _skill_system():
    skills = {
        "windless_roar": Skill.from_dict(
            {
                "id": "windless_roar",
                "name": "Windless Roar",
                "type": "active",
                "effect": "debuff_attack",
                "scaling": 1.15,
                "cooldown": 3,
                "qi_cost": 10,
            }
        )
    }
    return SkillSystem(skills)


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


def test_quest_reputation_reward_applies():
    quests = QuestSystem(
        [
            {
                "id": "renown",
                "title": "Renown",
                "auto_start": True,
                "objectives": [{"type": "defeat", "target": "any", "count": 1, "text": "x"}],
                "rewards": {"reputation": 10},
            }
        ]
    )
    player = Player(name="Tester")
    inventory = _inventory()

    completed = quests.notify("defeat", player, inventory)

    assert len(completed) == 1
    assert player.reputation == 10
    assert completed[0]["rewards"]["reputation"] == 10


def test_completing_quest_unlocks_chained_quest():
    quests = QuestSystem(
        [
            {
                "id": "first",
                "title": "First",
                "auto_start": True,
                "objectives": [{"type": "defeat", "target": "any", "count": 1, "text": "x"}],
                "rewards": {},
            },
            {
                "id": "second",
                "title": "Second",
                "auto_start": False,
                "requires": {"completed": ["first"]},
                "objectives": [{"type": "defeat", "target": "any", "count": 1, "text": "x"}],
                "rewards": {},
            },
        ]
    )
    player = Player(name="Tester")
    inventory = _inventory()

    snap = {q["id"]: q for q in quests.snapshot()}
    assert snap["second"]["status"] == "locked"

    completed = quests.notify("defeat", player, inventory)  # completes first, unlocks second

    assert completed[0]["id"] == "first"
    snap = {q["id"]: q for q in quests.snapshot()}
    assert snap["first"]["status"] == "completed"
    assert snap["second"]["status"] == "active"


def test_check_unlocks_honours_reputation_and_location():
    quests = QuestSystem(
        [
            {
                "id": "gated",
                "title": "Gated",
                "auto_start": False,
                "requires": {"min_reputation": 20, "location": "nine_furnace_kingdom"},
                "objectives": [{"type": "defeat", "target": "any", "count": 1, "text": "x"}],
                "rewards": {},
            },
        ]
    )

    locked = Player(name="Tester", reputation=50, current_location="azure_village")
    assert quests.check_unlocks(locked) == []  # wrong location

    ready = Player(name="Tester", reputation=50, current_location="nine_furnace_kingdom")
    assert quests.check_unlocks(ready) == ["gated"]
    assert quests.check_unlocks(ready) == []  # idempotent

    low_rep = Player(name="Tester", reputation=5, current_location="nine_furnace_kingdom")
    assert quests.check_unlocks(low_rep) == []


def test_quest_skill_reward_teaches_skill():
    quests = QuestSystem(
        [
            {
                "id": "technique",
                "title": "Technique",
                "auto_start": True,
                "objectives": [{"type": "defeat", "target": "any", "count": 1, "text": "x"}],
                "rewards": {"skills": ["windless_roar"]},
            }
        ],
        skill_system=_skill_system(),
    )
    player = Player(name="Tester")
    inventory = _inventory()

    completed = quests.notify("defeat", player, inventory)

    assert completed[0]["rewards"]["skills"] == ["windless_roar"]
    assert "windless_roar" in player.skills


def test_quest_manual_reward_grants_manual_item():
    quests = QuestSystem(
        [
            {
                "id": "manual_gift",
                "title": "Manual Gift",
                "auto_start": True,
                "objectives": [{"type": "defeat", "target": "any", "count": 1, "text": "x"}],
                "rewards": {"manuals": {"spirit_palm_manual": 1}},
            }
        ]
    )
    player = Player(name="Tester")
    inventory = _inventory()

    completed = quests.notify("defeat", player, inventory)

    assert player.inventory.get("spirit_palm_manual", 0) == 1
    assert completed[0]["rewards"]["items"]["spirit_palm_manual"] == 1
