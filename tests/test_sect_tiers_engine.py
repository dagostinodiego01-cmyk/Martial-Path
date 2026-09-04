"""Engine-level story-tier progression: arrival tracking, sect tier gating, halls."""
from game.core.constants import EventType
from game.core.game_engine import GameEngine


def _arrive(engine: GameEngine, location_id: str) -> None:
    """Place the player at a location through the engine's arrival path."""
    engine.player.current_location = location_id
    engine._note_arrival(location_id)


def test_arrival_raises_max_story_tier_and_persists_to_save():
    engine = GameEngine.new_game(seed=1)
    assert engine.player.max_story_tier == 1  # starting wilds

    _arrive(engine, "lin_academy")
    assert engine.player.max_story_tier == 2

    _arrive(engine, "divine_phoenix_island")
    assert engine.player.max_story_tier == 4
    assert engine.player.to_save_dict()["max_story_tier"] == 4


def test_loaded_save_keeps_story_tier_progress():
    engine = GameEngine.new_game(seed=1)
    _arrive(engine, "seven_profound_valleys_inner")
    engine.save_game("tier-progress")

    fresh = GameEngine.new_game(seed=999)
    fresh.load_game("tier-progress")

    assert fresh.player.current_location == "seven_profound_valleys_inner"
    assert fresh.player.max_story_tier == 3


def test_story_tier_gates_high_tier_sect_join():
    engine = GameEngine.new_game(seed=1)
    _arrive(engine, "asura_divine_kingdom")  # story tier 5 location
    player = engine.player
    player.reputation = -50
    player.cultivation_state.body.realm_id = "body_pulse_condensation"

    # Max story tier is now 5, so the tier-5 Asura sect admits this player.
    result = engine.sects.join(player, "asura_divine_kingdom")
    assert result["event"] == EventType.SECT_JOINED
    assert result["tier"] == 5

    # A player who never progressed past the early game is turned away.
    novice = GameEngine.new_game(seed=2).player
    novice.current_location = "asura_divine_kingdom"
    novice.reputation = -50
    novice.cultivation_state.body.realm_id = "body_pulse_condensation"
    blocked = engine.sects.join(novice, "asura_divine_kingdom")
    assert blocked["event"] == EventType.ERROR
    assert blocked["reason"] == "STORY_TIER_TOO_LOW"
    assert blocked["required_story_tier"] == 5
    assert blocked["story_tier"] == 1


def test_sect_hall_lists_and_sells_tier_techniques():
    engine = GameEngine.new_game(seed=1)
    _arrive(engine, "lin_academy")
    player = engine.player

    view = engine.sects.sect_view(player, "lin_academy")
    assert view["event"] == EventType.SECTS
    assert view["sect"]["tier"] == 1
    techniques = view["sect"]["techniques"]
    assert techniques, "tier-1 sect must offer techniques"
    assert all("price" in technique for technique in techniques)

    # Join, fund, and buy an unknown technique through the engine route.
    assert engine.sects.join(player, "lin_academy")["event"] == EventType.SECT_JOINED
    target = next(t for t in techniques if t["skill_id"] not in player.skills)
    price = target["price"]
    if "gold" in price:
        player.gold += price["gold"]
    else:
        player.inventory["spirit_stone"] = player.inventory.get("spirit_stone", 0) + price["spirit_stone"]
    bought = engine.process_action(
        {"action": "LEARN_SKILL", "sect_id": "lin_academy", "skill_id": target["skill_id"]}
    )
    assert bought["event"] == EventType.SKILL_LEARNED
    assert bought["source"] == "sect"
    assert target["skill_id"] in player.skills


def test_sect_view_requires_the_sect_be_present():
    engine = GameEngine.new_game(seed=1)
    _arrive(engine, "outer_forest")

    result = engine.process_action({"action": "SECTS", "sect_id": "lin_academy"})
    assert result["event"] == EventType.ERROR
    assert result["reason"] == "SECT_NOT_AVAILABLE"
