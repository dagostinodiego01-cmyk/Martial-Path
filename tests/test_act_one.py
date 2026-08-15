"""Campaign Act 1 (ROADMAP D.1): quest chain, tournament, and Dao awakening."""
from game.core.constants import Action, EventType
from game.core.game_engine import GameEngine


def test_act_one_chain_is_a_real_chain():
    engine = GameEngine.new_game(seed=1)
    titles = {quest["id"]: quest for quest in engine.quests.snapshot()}
    for quest_id in (
        "act1_join_sect",
        "act1_first_rival",
        "act1_tournament",
        "act1_dao_awakening",
        "act1_conclusion",
    ):
        assert quest_id in titles, quest_id
    # Each link requires the previous one (a linear-but-branching spine).
    assert "act1_join_sect" in titles["act1_first_rival"]["requires"]["completed"]
    assert "act1_first_rival" in titles["act1_tournament"]["requires"]["completed"]
    assert "act1_tournament" in titles["act1_dao_awakening"]["requires"]["completed"]
    assert "act1_dao_awakening" in titles["act1_conclusion"]["requires"]["completed"]
    assert engine.quests.act_end("act1_conclusion") == "act_one"


def test_join_sect_objective_advances_on_join():
    engine = GameEngine.new_game(seed=1)
    # Completing the tutorial unlocks the join-sect beat.
    for _ in range(3):
        engine.quests.notify("defeat", engine.player, engine.inventory)
    assert engine.quests.objective_active("join_sect")


def test_tournament_objective_completes_on_bout_won():
    engine = GameEngine.new_game(seed=1)
    engine.quests._activate("act1_tournament")

    updates = engine.quests.notify("tournament", engine.player, engine.inventory)

    assert any(update["id"] == "act1_tournament" for update in updates)
    assert engine.quests.objective_completed("tournament")


def test_tournament_starts_combat_at_sect_location():
    engine = GameEngine.new_game(seed=1)
    engine.player.current_location = "lin_academy"  # a sect hub

    result = engine.process_action({"action": Action.TOURNAMENT})

    assert result["event"] == EventType.COMBAT
    assert result.get("tournament") is True
    assert engine._mode == "combat"


def test_tournament_unavailable_in_a_village():
    engine = GameEngine.new_game(seed=1)
    engine.player.current_location = "azure_village"

    result = engine.process_action({"action": Action.TOURNAMENT})

    assert result["event"] == EventType.ERROR
    assert result["reason"] == "NO_TOURNAMENT_HERE"


def test_dao_awakening_is_gated_and_one_shot():
    engine = GameEngine.new_game(seed=1)

    locked = engine.process_action({"action": Action.DAO_AWAKEN, "dao_id": "flame_dao"})
    assert locked["event"] == EventType.ERROR
    assert locked["reason"] == "DAO_AWAKENING_LOCKED"

    engine.quests._activate("act1_dao_awakening")
    result = engine.process_action({"action": Action.DAO_AWAKEN, "dao_id": "flame_dao"})
    assert result["event"] == EventType.DAO_AWAKENED
    assert engine.player.dao_id == "flame_dao"
    assert engine.quests.objective_completed("dao_awakening")

    again = engine.process_action({"action": Action.DAO_AWAKEN, "dao_id": "sword_dao"})
    assert again["event"] == EventType.ERROR
    assert again["reason"] == "DAO_ALREADY_AWAKENED"


def test_dao_view_lists_catalogue_and_current():
    engine = GameEngine.new_game(seed=1)
    result = engine.process_action({"action": Action.DAO_VIEW})

    assert result["event"] == EventType.DAO_VIEW
    assert result["current_dao_id"] == "sword_dao"
    assert len(result["daos"]) >= 12
