"""Tests for sect joining, path assignment, join gating, tiers, and halls."""
from game.core.constants import EventType
from game.models.player import Player
from game.models.skill import Skill
from game.systems.sect_system import SectSystem
from game.systems.skill_system import SkillSystem

BODY_REALMS = {
    "realms": [
        {"id": "mortal", "order": 0},
        {"id": "flesh_training", "order": 2},
        {"id": "bone_forging", "order": 5},
        {"id": "body_pulse_condensation", "order": 6},
    ]
}

SECTS = [
    {
        "id": "divine_phoenix_island",
        "display_name": "Divine Phoenix Island",
        "path": "Divine Phoenix",
        "location_ids": ["divine_phoenix_island"],
        "tier": 4,
        "join_requirements": {"min_reputation": 15, "min_body_realm": "bone_forging"},
        "contribution_ranks": ["outer_disciple", "inner_disciple"],
        "techniques": [
            {"skill_id": "phoenix_sword_art", "price": {"spirit_stone": 2}},
        ],
    },
    {
        "id": "asura_kingdom",
        "display_name": "Asura Divine Kingdom",
        "path": "Asura Path",
        "location_ids": ["asura_divine_kingdom"],
        "tier": 5,
        "join_requirements": {"max_reputation": -10, "min_body_realm": "body_pulse_condensation"},
        "contribution_ranks": ["blood_disciple"],
        "techniques": [
            {"skill_id": "phoenix_fist", "price": {"spirit_stone": 2}, "required_path": "Divine Phoenix"},
        ],
    },
]

SKILLS = {
    "phoenix_sword_art": Skill.from_dict({"id": "phoenix_sword_art", "name": "Phoenix Sword Art", "type": "active", "qi_cost": 10, "cooldown": 3}),
    "phoenix_fist": Skill.from_dict({"id": "phoenix_fist", "name": "Phoenix Fist", "type": "active", "qi_cost": 10, "cooldown": 3}),
}


def _system() -> SectSystem:
    skills = dict(SKILLS)
    return SectSystem(SECTS, BODY_REALMS, skills=skills, skill_system=SkillSystem(skills))


def _player(location="divine_phoenix_island", reputation=20, realm="bone_forging", max_story_tier=4) -> Player:
    player = Player(name="Tester", current_location=location, reputation=reputation)
    player.cultivation_state.body.realm_id = realm
    player.max_story_tier = max_story_tier
    return player


def test_join_sets_player_path_and_starting_rank():
    system = _system()

    result = system.join(_player(), "divine_phoenix_island")

    assert result["event"] == EventType.SECT_JOINED
    assert result["path"] == "Divine Phoenix"
    assert result["rank"] == "outer_disciple"


def test_join_gated_by_body_realm():
    system = _system()

    result = system.join(_player(realm="flesh_training"), "divine_phoenix_island")

    assert result["event"] == EventType.ERROR
    assert result["reason"] == "REALM_TOO_LOW"


def test_join_gated_by_min_reputation():
    system = _system()

    result = system.join(_player(reputation=5), "divine_phoenix_island")

    assert result["event"] == EventType.ERROR
    assert result["reason"] == "REPUTATION_TOO_LOW"


def test_join_gated_by_max_reputation():
    system = _system()

    result = system.join(_player(location="asura_divine_kingdom", reputation=0, realm="body_pulse_condensation"), "asura_kingdom")

    assert result["event"] == EventType.ERROR
    assert result["reason"] == "REPUTATION_TOO_HIGH"

    joined = system.join(_player(location="asura_divine_kingdom", reputation=-20, realm="body_pulse_condensation"), "asura_kingdom")
    assert joined["event"] == EventType.SECT_JOINED
    assert joined["path"] == "Asura Path"


def test_join_gated_by_location():
    system = _system()

    result = system.join(_player(location="outer_forest"), "divine_phoenix_island")

    assert result["event"] == EventType.ERROR
    assert result["reason"] == "SECT_NOT_AVAILABLE"


def test_join_same_sect_again_is_rejected():
    system = _system()
    player = _player()
    player.path = "Divine Phoenix"

    result = system.join(player, "divine_phoenix_island")

    assert result["event"] == EventType.ERROR
    assert result["reason"] == "ALREADY_JOINED"


def test_sects_for_location_filters_by_location():
    system = _system()

    assert [s["id"] for s in system.sects_for_location("divine_phoenix_island")] == ["divine_phoenix_island"]
    assert system.sects_for_location("outer_forest") == []


def test_summary_exposes_tier_and_view_lists_hall():
    system = _system()

    assert system.sects_for_location("divine_phoenix_island")[0]["tier"] == 4
    view = system.sect_view(_player(), "divine_phoenix_island")
    techniques = view["sect"]["techniques"]
    assert [t["skill_id"] for t in techniques] == ["phoenix_sword_art"]
    assert techniques[0]["price"] == {"spirit_stone": 2}
    assert techniques[0]["already_known"] is False
    assert techniques[0]["affordable"] is False  # no spirit stones yet


def test_story_tier_gate_blocks_low_progress_player():
    system = _system()
    sects = [
        {
            "id": "high_sect",
            "display_name": "High Sect",
            "path": "High Path",
            "location_ids": ["divine_phoenix_island"],
            "tier": 5,
            "join_requirements": {"min_story_tier": 5, "min_body_realm": "mortal"},
            "contribution_ranks": ["outer_disciple"],
        }
    ]
    gated = SectSystem(sects, BODY_REALMS)

    blocked = gated.join(_player(max_story_tier=2), "high_sect")
    assert blocked["event"] == EventType.ERROR
    assert blocked["reason"] == "STORY_TIER_TOO_LOW"
    assert blocked["required_story_tier"] == 5

    allowed = gated.join(_player(max_story_tier=5), "high_sect")
    assert allowed["event"] == EventType.SECT_JOINED


def test_join_result_reports_tier():
    system = _system()

    result = system.join(_player(), "divine_phoenix_island")

    assert result["tier"] == 4


def test_learn_requires_sect_membership():
    system = _system()
    player = _player()
    player.inventory["spirit_stone"] = 10

    blocked = system.learn(player, "phoenix_sword_art", "divine_phoenix_island")
    assert blocked["event"] == EventType.ERROR
    assert blocked["reason"] == "SECT_NOT_JOINED"
    assert "phoenix_fist" not in player.skills
    assert player.inventory["spirit_stone"] == 10  # nothing spent


def test_learn_enforces_path_lock():
    system = _system()
    player = _player(location="asura_divine_kingdom", reputation=-20, realm="body_pulse_condensation")
    player.path = "Asura Path"  # member, but the art belongs to another lineage
    player.inventory["spirit_stone"] = 10

    blocked = system.learn(player, "phoenix_fist", "asura_kingdom")
    assert blocked["event"] == EventType.ERROR
    assert blocked["reason"] == "PATH_LOCKED"
    assert blocked["required_path"] == "Divine Phoenix"
    assert "phoenix_fist" not in player.skills
    assert player.inventory["spirit_stone"] == 10  # nothing spent


def test_learn_spends_and_teaches_for_member():
    system = _system()
    player = _player()
    player.path = "Divine Phoenix"
    player.inventory["spirit_stone"] = 10

    result = system.learn(player, "phoenix_sword_art", "divine_phoenix_island")

    assert result["event"] == EventType.SKILL_LEARNED
    assert result["source"] == "sect"
    assert result["sect_id"] == "divine_phoenix_island"
    assert "phoenix_sword_art" in player.skills
    assert player.inventory["spirit_stone"] == 8


def test_learn_rejects_unoffered_and_unknown():
    system = _system()
    player = _player()
    player.path = "Divine Phoenix"

    assert system.learn(player, "iron_fist", "divine_phoenix_island")["reason"] == "TECHNIQUE_NOT_OFFERED"
    assert system.learn(player, "no_such_skill", "divine_phoenix_island")["reason"] == "TECHNIQUE_NOT_OFFERED"


def test_joined_sect_view_for_member_and_stranger():
    system = _system()

    stranger = system.joined_sect_view(_player())
    assert stranger == {}

    member = _player()
    member.path = "Divine Phoenix"
    view = system.joined_sect_view(member)
    assert view["sect_id"] == "divine_phoenix_island"
    assert view["tier"] == 4
    assert len(view["techniques"]) == 1
