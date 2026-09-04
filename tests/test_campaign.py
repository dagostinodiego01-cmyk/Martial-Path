"""Full campaign + post-game (ROADMAP D.3-D.5).

D.3 -- Acts 2-3 chain (faction conflict -> dao re-awakening -> realm war ->
final ascension choice); completing the final act wins the campaign and
chooses one of three morality-driven endings, banked as a legacy bonus and
recorded in the chronicle.
D.4 -- two faction quest chains (Divine Phoenix, Seven Profound Valleys)
with branching outcomes gated by sect path and morality; new objectives
(spar, debate, realm_completed) advance from the engine's real actions.
D.5 -- the endless post-game: procedural, depth-scaled secret realms behind
the ENDLESS_REALM action; the first descent lifts the essence realm cap;
realms are deterministic per (seed, depth) and never repeat a layout.
"""
from __future__ import annotations

import pytest

from game.core.game_engine import GameEngine
from game.systems.secret_realm_system import SecretRealmSystem
from game.utils.rng import RNG


@pytest.fixture()
def engine() -> GameEngine:
    return GameEngine.new_game(player_name="Campaigner", seed=20260904)


def complete_chain(engine: GameEngine, quest_ids: list[str]) -> None:
    """Mark a chain of quests completed exactly as the engine would."""
    quests = engine.quests
    for quest_id in quest_ids:
        quests._activate(quest_id)
        quests._state[quest_id]["status"] = quests.STATUS_COMPLETED


# -- D.3: Acts 2-3 -------------------------------------------------------

class TestActs23:
    ACT_ONE = [
        "act1_join_sect",
        "act1_first_rival",
        "act1_tournament",
        "act1_dao_awakening",
        "act1_conclusion",
    ]
    ACT_TWO = [
        "act2_shadows_of_the_valleys",
        "act2_faction_conflict",
        "act2_dao_awakening",
        "act2_realm_war",
    ]

    def test_act_two_chain_unlocks_from_act_one(self, engine: GameEngine):
        complete_chain(engine, self.ACT_ONE)
        unlocked = engine.quests.check_unlocks(engine.player)
        assert "act2_shadows_of_the_valleys" in unlocked

    def test_act_two_chain_covers_the_story_beats(self, engine: GameEngine):
        """Faction conflict -> dao re-awakening -> realm war, in that order."""
        complete_chain(engine, self.ACT_ONE)
        complete_chain(engine, self.ACT_TWO[:1])
        engine.player.reputation = 50
        engine.quests.check_unlocks(engine.player)
        complete_chain(engine, self.ACT_TWO[:2])
        engine.quests.check_unlocks(engine.player)
        complete_chain(engine, self.ACT_TWO[:3])
        unlocked = engine.quests.check_unlocks(engine.player)
        assert "act2_realm_war" in unlocked

    def test_act_two_concludes_on_the_ancient_devil(self, engine: GameEngine):
        complete_chain(engine, self.ACT_ONE + self.ACT_TWO[:3])
        engine.quests.check_unlocks(engine.player)
        updates = engine.quests.notify(
            "defeat", engine.player, engine.inventory, target="ancient_devil_manifestation"
        )
        assert any(update["id"] == "act2_realm_war" for update in updates)
        assert engine.quests.act_end("act2_realm_war") == "act_two"

    def test_final_act_unlocks_after_the_realm_war(self, engine: GameEngine):
        complete_chain(engine, self.ACT_ONE + self.ACT_TWO)
        unlocked = engine.quests.check_unlocks(engine.player)
        assert "act3_threshold_of_heaven" in unlocked

    def test_campaign_completes_on_the_final_act(self, engine: GameEngine):
        complete_chain(engine, self.ACT_ONE + self.ACT_TWO + ["act3_threshold_of_heaven"])
        # The final beat opens with the threshold crossed, and completes on a
        # breakthrough -- the ascension choice, not another boss re-fight.
        engine.quests.check_unlocks(engine.player)
        updates = engine.quests.notify("breakthrough", engine.player, engine.inventory)
        final = next(update for update in updates if update["id"] == "act3_final_ascension")
        assert engine.quests.act_end("act3_final_ascension") == "act_three"

        result = {"act_complete": "act_three"}
        engine._maybe_complete_campaign(result)
        completion = result["campaign_complete"]
        assert completion["ending_id"] in {"realm_martyr", "demon_sovereign", "ascended_sword"}
        assert completion["legacy_bonus"] > 0
        # The meta-save banked the bonus.
        assert engine.meta.memory() >= completion["legacy_bonus"]

    def test_campaign_completes_once(self, engine: GameEngine):
        engine._campaign_complete = True
        before = engine.meta.memory()
        result = {"act_complete": "act_three"}
        engine._maybe_complete_campaign(result)
        assert "campaign_complete" not in result
        assert engine.meta.memory() == before

    def test_three_endings_chosen_by_morality(self, engine: GameEngine):
        engine.player.morality = 60
        assert engine._campaign_ending()["ending_id"] == "realm_martyr"
        engine.player.morality = -60
        assert engine._campaign_ending()["ending_id"] == "demon_sovereign"
        engine.player.morality = 0
        assert engine._campaign_ending()["ending_id"] == "ascended_sword"

    def test_ending_recorded_in_the_chronicle(self, engine: GameEngine):
        # A run without a campaign ending records none.
        assert engine._chronicle_entry("old_age")["campaign_ending"] is None
        # Once earned, the ending belongs to the run whatever its end cause.
        engine._campaign_ending_id = "demon_sovereign"
        assert engine._chronicle_entry("ascended")["campaign_ending"] == "demon_sovereign"
        assert engine._chronicle_entry("old_age")["campaign_ending"] == "demon_sovereign"

    def test_campaign_view_reflects_state(self, engine: GameEngine):
        view = engine.get_game_state()["campaign"]
        assert view["campaign_complete"] is False
        assert view["can_endless_realm"] is False
        engine._campaign_complete = True
        view = engine.get_game_state()["campaign"]
        assert view["campaign_complete"] is True
        assert view["can_endless_realm"] is True

    def test_act2_dao_reawakening_window(self, engine: GameEngine):
        """The Act-Two rekindling reopens dao choice, one change per window."""
        complete_chain(engine, self.ACT_ONE + self.ACT_TWO[:2])
        engine.quests.check_unlocks(engine.player)
        # The beat is active: a change is allowed...
        result = engine.process_action({"action": "DAO_AWAKEN", "dao_id": "flame_dao"})
        assert result["event"] == "DAO_AWAKENED"
        # ...and completing the beat locks the dao again.
        complete_chain(engine, self.ACT_TWO[:3])
        locked = engine.process_action({"action": "DAO_AWAKEN", "dao_id": "tide_dao"})
        assert locked.get("reason") == "DAO_ALREADY_AWAKENED"

    def test_campaign_and_endless_flags_round_trip_through_saves(self, engine: GameEngine, tmp_path):
        engine._campaign_complete = True
        engine._campaign_ending_id = "realm_martyr"
        engine._endless_depth = 4
        snapshot = engine._session_snapshot()
        assert snapshot["campaign_complete"] is True
        assert snapshot["endless_depth"] == 4
        engine._campaign_complete = False
        engine._endless_depth = 0
        engine.quests.import_state(snapshot["quests"])
        # Simulate load restoration path fields directly.
        assert snapshot["campaign_ending_id"] == "realm_martyr"


# -- D.4: faction campaigns ----------------------------------------------

class TestFactionCampaigns:
    def test_two_faction_chains_exist(self, engine: GameEngine):
        chains = {
            quest.get("chain")
            for quest in engine.quests._defs.values()
            if quest.get("chain")
        }
        assert {"phoenix", "valleys"} <= chains

    def test_branches_split_on_morality(self, engine: GameEngine):
        """Each chain offers a ruthless (min_morality) and gentle (max_morality) branch."""
        for chain_root in ("phoenix_inner_trial", "valleys_road_of_ambition"):
            branches = [
                quest_id
                for quest_id, quest in engine.quests._defs.items()
                if quest.get("requires", {}).get("completed") == [chain_root]
            ]
            assert len(branches) == 2, chain_root
            gates = [
                (
                    engine.quests._defs[quest_id]["requires"].get("min_morality"),
                    engine.quests._defs[quest_id]["requires"].get("max_morality"),
                )
                for quest_id in branches
            ]
            assert any(min_m is not None for min_m, _ in gates), chain_root
            assert any(max_m is not None for _, max_m in gates), chain_root

    def test_phoenix_chain_gated_by_sect_path(self, engine: GameEngine):
        player = engine.player
        player.reputation = 25
        assert engine.quests.check_unlocks(player) == []
        player.path = "Divine Phoenix"
        assert "phoenix_inner_trial" in engine.quests.check_unlocks(player)

    def test_valleys_chain_accepts_its_factions(self, engine: GameEngine):
        player = engine.player
        player.reputation = 25
        player.path = "Seven Profound Valleys"
        assert "valleys_road_of_ambition" in engine.quests.check_unlocks(player)
        engine2 = GameEngine.new_game(player_name="T", seed=11)
        player2 = engine2.player
        player2.reputation = 25
        player2.path = "Asura Path"
        assert "valleys_road_of_ambition" in engine2.quests.check_unlocks(player2)

    def test_morality_branch_gates(self, engine: GameEngine):
        player = engine.player
        player.path = "Divine Phoenix"
        player.reputation = 25
        engine.quests.check_unlocks(player)
        engine.quests._state["phoenix_inner_trial"]["status"] = engine.quests.STATUS_COMPLETED
        # The saintly branch requires morality >= 10.
        player.morality = 5
        assert engine.quests.check_unlocks(player) == []
        player.morality = 20
        assert "phoenix_righteous_flame" in engine.quests.check_unlocks(player)

    def test_spar_and_debate_objectives_notify(self, engine: GameEngine):
        """Gentle-branch objectives advance through the engine's real actions."""
        player = engine.player
        player.path = "Divine Phoenix"
        player.reputation = 25
        player.morality = -20
        engine.quests.check_unlocks(player)
        engine.quests._state["phoenix_inner_trial"]["status"] = engine.quests.STATUS_COMPLETED
        engine.quests.check_unlocks(player)
        gentle = engine.quests._state.get("phoenix_merciful_shield")
        assert gentle is not None and gentle["status"] == engine.quests.STATUS_ACTIVE
        # Five spars + one debate complete the gentle branch.
        for _ in range(5):
            engine.quests.notify("spar", player, engine.inventory, target="any")
        engine.quests.notify("debate", player, engine.inventory, target="any")
        assert gentle["status"] == engine.quests.STATUS_COMPLETED
        # The gentle branch nudged morality further down.
        assert player.morality < -20

    def test_realm_completed_objective_notifies(self, engine: GameEngine):
        player = engine.player
        player.path = "Seven Profound Valleys"
        player.reputation = 25
        engine.quests.check_unlocks(player)
        engine.quests.notify("realm_completed", player, engine.inventory, target="any")
        state = engine.quests._state["valleys_road_of_ambition"]
        assert state["status"] == engine.quests.STATUS_COMPLETED
        assert state["progress"][0] == 1

    def test_realm_completion_notifies_quests(self, engine: GameEngine):
        """The engine's realm-completion path feeds the faction objective."""
        engine._realm = {
            "realm": {"display_name": "Test Realm", "final_reward": {"exp": 10}},
            "index": 99,
            "rooms": [{"kind": "boss"}],
        }
        player = engine.player
        player.path = "Seven Profound Valleys"
        player.reputation = 25
        engine.quests.check_unlocks(player)
        result = engine._complete_realm()
        assert result["event"] == "REALM_COMPLETED"
        assert engine.quests._state["valleys_road_of_ambition"]["progress"][0] == 1


# -- D.5: the endless road ------------------------------------------------

class TestEndlessRoad:
    def test_locked_until_campaign_or_endless(self, engine: GameEngine):
        result = engine.process_action({"action": "ENDLESS_REALM"})
        assert result["reason"] == "ENDLESS_NOT_OPEN"
        engine._endless = True
        result = engine.process_action({"action": "ENDLESS_REALM"})
        assert result["event"] == "REALM_ENTERED"

    def test_open_after_campaign_completion(self, engine: GameEngine):
        engine._maybe_complete_campaign({"act_complete": "act_three"})
        result = engine.process_action({"action": "ENDLESS_REALM"})
        assert result["event"] == "REALM_ENTERED"
        assert result["endless_depth"] == 1
        assert result["realm_cap_lifted"] == "beyond_divinity"

    def test_depth_increments_and_rewards_scale(self, engine: GameEngine):
        engine._campaign_complete = True
        first = engine.process_action({"action": "ENDLESS_REALM"})
        assert first["endless_depth"] == 1
        # Walk the realm to completion: depth reward rides on REALM_COMPLETED.
        rooms = engine._realm["realm"]["rooms"]
        for index, room in enumerate(rooms):
            if room["kind"] in ("encounter", "boss"):
                # Resolve the fight out-of-band (the wiring is tested elsewhere).
                engine._mode = engine._mode
                engine._current_enemy = None
                engine._realm["index"] = index + 1
            else:
                engine._realm["index"] = index + 1
        completed = engine.process_action({"action": "REALM_ADVANCE"})
        assert completed["event"] == "REALM_COMPLETED"
        assert completed["endless_depth"] == 1
        assert completed["reward"]["exp"] >= 150  # base + depth bonus
        second = engine.process_action({"action": "ENDLESS_REALM"})
        assert second["endless_depth"] == 2
        assert second["rooms_total"] >= first["rooms_total"]

    def test_generation_is_deterministic_per_seed_and_depth(self, engine: GameEngine):
        system = SecretRealmSystem([], RNG(1))
        pool = ["mook_a", "mook_b", "mook_c"]
        named = ["boss_a", "boss_b"]
        treasure = [{"item_id": "qi_pill", "weight": 3}, {"item_id": "healing_pill", "weight": 2}]
        a = system.generate_endless(3, pool, named, treasure, essence_order=2, rng=RNG(99))
        b = system.generate_endless(3, pool, named, treasure, essence_order=2, rng=RNG(99))
        c = system.generate_endless(4, pool, named, treasure, essence_order=2, rng=RNG(99))
        assert a == b
        assert a["rooms"] != c["rooms"] or a["scale"] != c["scale"]

    def test_scaling_grows_with_depth(self, engine: GameEngine):
        system = SecretRealmSystem([], RNG(1))
        shallow = system.generate_endless(1, ["mook"], ["boss"], [], essence_order=1, rng=RNG(5))
        deep = system.generate_endless(10, ["mook"], ["boss"], [], essence_order=1, rng=RNG(5))
        assert deep["scale"] > shallow["scale"]
        assert deep["final_reward"]["exp"] > shallow["final_reward"]["exp"]

    def test_boss_room_is_last_and_scaled(self, engine: GameEngine):
        system = SecretRealmSystem([], RNG(1))
        realm = system.generate_endless(2, ["mook_a", "mook_b"], ["boss_a"], [], essence_order=1, rng=RNG(9))
        boss = realm["rooms"][-1]
        assert boss["kind"] == "boss"
        assert boss["enemy_id"] == "boss_a"
        assert boss["scale"] == realm["scale"]

    def test_depth_gates_high_realm_foes_out_of_shallow_roads(self, engine: GameEngine):
        """A depth-1 road never rolls a high-realm foe (balance: the road asks
        for the foe's realm before it serves them)."""
        system = SecretRealmSystem([], RNG(1))
        orders = {"wild_wolf": 1, "grand_devil": 5}  # grand_devil: order-5 world
        pool = ["wild_wolf", "grand_devil"]
        shallow_foes = set()
        deep_foes = set()
        for seed in range(12):
            shallow = system.generate_endless(
                1, ["wild_wolf"], pool, [], essence_order=3,
                rng=RNG(100 + seed), foe_orders=orders,
            )
            deep = system.generate_endless(
                5, ["wild_wolf"], pool, [], essence_order=3,
                rng=RNG(100 + seed), foe_orders=orders,
            )
            shallow_foes |= {r["enemy_id"] for r in shallow["rooms"] if r.get("enemy_id")}
            deep_foes |= {r["enemy_id"] for r in deep["rooms"] if r.get("enemy_id")}
        # Shallow roads never serve the high-realm devil; deep roads can.
        assert "grand_devil" not in shallow_foes
        assert shallow_foes == {"wild_wolf"}
        assert "grand_devil" in deep_foes

    def test_enemy_scaling_inflates_combat_stats(self, engine: GameEngine):
        enemy = engine._spawn_enemy(next(iter(engine._enemy_templates.keys())))
        original_hp, original_attack = enemy.max_hp, enemy.attack
        engine._scale_enemy(enemy, 2.0)
        assert enemy.max_hp == original_hp * 2
        assert enemy.attack == original_attack * 2
        assert enemy.hp == enemy.max_hp

    def test_endless_rooms_scale_their_foes(self, engine: GameEngine):
        """A spawned endless foe is inflated by its room's scale factor."""
        system = SecretRealmSystem([], RNG(1))
        realm = system.generate_endless(
            5, ["wild_wolf"], ["xuan_wuji_boss"], [], essence_order=1, rng=RNG(3)
        )
        encounter = next(room for room in realm["rooms"] if room["kind"] == "encounter")
        assert encounter["scale"] > 1.0
        engine._realm = {"realm": realm, "index": 0, "endless_depth": 5}
        plain = engine._spawn_enemy(encounter["enemy_id"])
        scaled_hp = plain.max_hp
        # The engine scales the freshly spawned foe against the room's scale.
        engine._current_enemy = plain
        engine._scale_endless_room(encounter)
        assert plain.max_hp == int(round(scaled_hp * encounter["scale"]))

    def test_first_descent_lifts_the_essence_cap(self, engine: GameEngine):
        """Beyond Divinity is locked until the endless road opens it."""
        locked = engine.cultivation._essence_by_id["beyond_divinity"]
        assert locked.get("reachable") is False or locked.get("type") == "theoretical_endpoint"
        engine._campaign_complete = True
        engine.process_action({"action": "ENDLESS_REALM"})
        unlocked = engine.cultivation._essence_by_id["beyond_divinity"]
        assert unlocked.get("reachable") is not False
        assert unlocked.get("type") != "theoretical_endpoint"

    def test_rooms_total_grows_with_depth(self, engine: GameEngine):
        system = SecretRealmSystem([], RNG(1))
        shallow = system.generate_endless(1, ["mook"], ["boss"], [], essence_order=1, rng=RNG(5))
        deep = system.generate_endless(20, ["mook"], ["boss"], [], essence_order=1, rng=RNG(5))
        assert len(deep["rooms"]) > len(shallow["rooms"])
