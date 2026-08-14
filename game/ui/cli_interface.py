"""Command-line interface.

Owns the input/output loop. It converts engine result dictionaries into text and
prints them; it never contains gameplay rules. Every ``print`` in the entire
codebase lives in this file (plus the banner helpers below).
"""
from __future__ import annotations

from typing import Any, Dict

from game.application.command_router import CommandRouter
from game.core.constants import EventType
from game.core.game_engine import GameEngine


class CLIInterface:
    """Renders the game to a terminal and forwards input to the engine."""

    def __init__(self, engine: GameEngine, router: CommandRouter) -> None:
        self._engine = engine
        self._router = router
        # Map each engine event type to the method that renders it.
        self._formatters = {
            EventType.TRAIN_RESULT: self._fmt_train,
            EventType.BREAKTHROUGH_RESULT: self._fmt_breakthrough,
            EventType.EXPLORE_RESULT: self._fmt_explore,
            EventType.COMBAT: self._fmt_combat_start,
            EventType.COMBAT_TURN: self._fmt_combat_turn,
            EventType.COMBAT_END: self._fmt_combat_end,
            EventType.LOOT: self._fmt_loot,
            EventType.SPECIAL: self._fmt_special,
            EventType.STATUS: self._fmt_status,
            EventType.INVENTORY: self._fmt_inventory,
            EventType.ITEM_USED: self._fmt_item_used,
            EventType.EQUIP_ITEM_RESULT: self._fmt_equipment_result,
            EventType.UNEQUIP_ITEM_RESULT: self._fmt_equipment_result,
            EventType.STARTING_FATE_ROLLED: self._fmt_starting_fate,
            EventType.STARTING_FATE_ACCEPTED: self._fmt_starting_fate,
            EventType.CHARACTER_ENCOUNTER: self._fmt_character_encounter,
            EventType.CHARACTER_INTERACTION: self._fmt_character_interaction,
            EventType.SECTS: self._fmt_sects,
            EventType.SECT_JOINED: self._fmt_sect_joined,
            EventType.MAP: self._fmt_map,
            EventType.BOON: self._fmt_boon,
            EventType.PLAYER_DIED: self._fmt_died,
            EventType.HELP: self._fmt_help,
            EventType.ERROR: self._fmt_error,
            EventType.QUIT: self._fmt_quit,
        }

    # -- main loop --------------------------------------------------------
    def run(self) -> None:
        """Run the interactive game loop until the player quits."""
        self._print_banner()
        try:
            name = input("Enter your cultivator's name: ").strip()
        except (EOFError, KeyboardInterrupt):
            name = ""
        self._engine.set_player_name(name or "Nameless Daozi")

        title = self._engine.get_game_state()["player"]["name"]
        self._p(f"\nThe long road of cultivation opens before {title}...")
        self._fmt_help({})

        while self._engine.is_running():
            try:
                raw = input(self._build_prompt())
            except (EOFError, KeyboardInterrupt):
                self._p("\nYou withdraw from the mortal world. Farewell.")
                break
            command = self._router.route(raw)
            result = self._engine.process_action(command)
            self._render(result)

    # -- rendering --------------------------------------------------------
    def _render(self, result: Dict[str, Any]) -> None:
        formatter = self._formatters.get(result.get("event"), self._fmt_generic)
        formatter(result)

    def _fmt_train(self, result: Dict[str, Any]) -> None:
        track = "Body" if result.get("track_id") == "body_transformation" else "Essence"
        self._p(result.get("player_message", f"You train your {track.lower()} cultivation."))
        exp_text = f", EXP +{result['exp_gained']}" if result.get("exp_gained") else ""
        self._p(f"{track} progress +{result['gained']}% (now {result['progress']}%){exp_text}.")
        if result.get("ready_to_breakthrough"):
            command = "breakthrough body" if result.get("track_id") == "body_transformation" else "breakthrough essence"
            self._p(f"This path is ready - type '{command}' to advance.")

    def _fmt_breakthrough(self, result: Dict[str, Any]) -> None:
        if result.get("success"):
            self._hr()
            self._p(f"BREAKTHROUGH! {result['previous']} -> {result['cultivation']}")
            if result.get("realm_changed"):
                self._p("You have ascended to a NEW REALM! Heaven and earth tremble.")
            gains = result.get("gains", {})
            self._p(f"  Max HP +{gains.get('max_hp', 0)} | Max Qi +{gains.get('max_qi', 0)} | "
                    f"ATK +{gains.get('attack', 0)} | DEF +{gains.get('defense', 0)}")
            self._hr()
            return
        reason = result.get("reason")
        if reason == "INSUFFICIENT_PROGRESS":
            self._p(f"You are not ready. Progress is only {result['progress']}% (need 100%).")
        elif "progress_lost" in result:
            self._p(f"The breakthrough FAILED! Your qi scatters. Progress -{result['progress_lost']}% "
                    f"(now {result['progress']}%).")
        else:
            self._p(result.get("player_message", f"The breakthrough cannot be attempted ({reason})."))

    def _fmt_explore(self, result: Dict[str, Any]) -> None:
        self._p(result.get("text", "You explore, but nothing happens."))

    def _fmt_combat_start(self, result: Dict[str, Any]) -> None:
        enemy = result["enemy"]
        self._hr()
        self._p(result.get("text", "A battle begins!"))
        self._p(f"  {enemy['name']} ({enemy.get('realm', 'Unknown Realm')}) - HP {enemy['hp']}/{enemy['max_hp']}, "
                f"ATK {enemy['attack']}, DEF {enemy['defense']}")
        self._p("  Commands: attack | skill <id> | use <id> | flee")
        self._hr()

    def _fmt_combat_turn(self, result: Dict[str, Any]) -> None:
        for event in result.get("turn_events", []):
            self._p("  " + self._describe_turn_event(event))
        self._p(f"  [You HP {result.get('player_hp')}/{result.get('player_max_hp')} | "
                f"{result.get('enemy_name')} HP {result.get('enemy_hp')}/{result.get('enemy_max_hp')}]")

    def _fmt_combat_end(self, result: Dict[str, Any]) -> None:
        for event in result.get("turn_events", []):
            self._p("  " + self._describe_turn_event(event))
        outcome = result.get("outcome")
        self._hr()
        if outcome == "VICTORY":
            self._p(f"VICTORY! You have slain the {result.get('enemy_name')}.")
            self._p(f"  EXP +{result.get('exp_reward', 0)}.")
            loot = result.get("loot", [])
            if loot:
                for entry in loot:
                    self._p(f"  Loot: {entry['name']} x{entry['count']}.")
            else:
                self._p("  The corpse yields no spoils.")
        elif outcome == "DEFEAT":
            penalty = result.get("penalty", {})
            self._p(f"DEFEAT... the {result.get('enemy_name')} overwhelms you.")
            self._p(f"  A passing elder rescues you. Progress lost: {penalty.get('progress_lost', 0)}%. "
                    f"You awaken with {penalty.get('revived_hp', 0)} HP.")
        elif outcome == "FLED":
            self._p(f"You escape from the {result.get('enemy_name')}, heart pounding.")
        self._hr()

    def _fmt_loot(self, result: Dict[str, Any]) -> None:
        self._p(f"You obtained {result['name']} x{result['count']} "
                f"(you now hold {result['total']}).")

    def _fmt_special(self, result: Dict[str, Any]) -> None:
        self._hr()
        self._p(result.get("text", "Something extraordinary happens."))
        if "progress_boost" in result:
            self._p(f"  Cultivation progress +{result['progress_boost']}% (now {result['progress']}%).")
        if result.get("restored"):
            self._p(f"  Fully restored! HP {result['hp']}, Qi {result['qi']}.")
        if "exp_gained" in result:
            self._p(f"  EXP +{result['exp_gained']} (total {result['exp']}).")
        self._hr()

    def _fmt_status(self, result: Dict[str, Any]) -> None:
        p = result["player"]
        cultivation = p.get("cultivation_state", {})
        body = cultivation.get("body_transformation", {})
        essence = cultivation.get("essence_gathering", {})
        balance = cultivation.get("balance", {})
        safety = cultivation.get("breakthrough_safety", {})
        self._hr()
        self._p(p["name"])
        self._p(f"  Body Transformation : {body.get('display_name', p.get('realm', '-'))}")
        self._p(f"    Progress {body.get('progress', p.get('progress', 0))}% | Foundation {body.get('foundation', 0)} | Strength {body.get('body_strength', 0)}")
        self._p(f"  Essence Gathering   : {essence.get('display_name', p.get('essence_cultivation', '-'))}")
        self._p(f"    Progress {essence.get('progress', 0)}% | Foundation {essence.get('foundation', 0)} | Dantian {essence.get('dantian_capacity', 0)}")
        self._p(f"  Balance  : {balance.get('status', '-')} | Safety {safety.get('level', '-')} ({safety.get('score', 0)})")
        self._p(f"  HP       : {p['hp']}/{p['max_hp']}")
        self._p(f"  Qi       : {p['qi']}/{p['max_qi']}")
        self._p(f"  ATK/DEF  : {p['attack']} / {p['defense']}")
        self._p(f"  EXP/Gold : {p['exp']} / {p['gold']}")
        skills = p.get("skills", [])
        if skills:
            self._p("  Skills   :")
            cooldowns = p.get("cooldowns", {})
            for skill in skills:
                cd = cooldowns.get(skill.get("id"), 0)
                cd_text = f" (cooldown {cd})" if cd else ""
                cost = f", {skill.get('qi_cost', 0)} qi" if skill.get("type") == "active" else ""
                self._p(f"    - {skill['name']} [{skill.get('type', '?')}{cost}]{cd_text}")
        self._hr()

    def _fmt_inventory(self, result: Dict[str, Any]) -> None:
        items = result.get("items", [])
        self._hr()
        if not items:
            self._p("Your storage ring is empty.")
        else:
            self._p("Inventory:")
            for entry in items:
                self._p(f"  - {entry['name']} x{entry['count']} "
                        f"[{entry['item_id']}] - {entry['description']}")
        self._hr()

    def _fmt_equipment_result(self, result: Dict[str, Any]) -> None:
        self._p(result.get("player_message", "Equipment changed."))
        self._p(f"  Slot: {result.get('slot', '-')}")
        stats = result.get("effective_stats", {})
        if stats:
            self._p(f"  Effective ATK/DEF: {stats.get('attack', '-')} / {stats.get('defense', '-')}")

    def _fmt_item_used(self, result: Dict[str, Any]) -> None:
        parts = [f"You use {result['name']}."]
        if result.get("healed"):
            parts.append(f"Recovered {result['healed']} HP (now {result.get('hp')}).")
        if result.get("qi_restored"):
            parts.append(f"Recovered {result['qi_restored']} Qi (now {result.get('qi')}).")
        if "progress_boost" in result:
            parts.append(f"Cultivation +{result['progress_boost']}% (now {result.get('progress')}%).")
        self._p(" ".join(parts))

    def _fmt_starting_fate(self, result: Dict[str, Any]) -> None:
        root = result.get("spiritual_root", {})
        physique = result.get("physique", {})
        self._hr()
        self._p(result.get("player_message", "Your starting fate has been revealed."))
        self._p(f"  Spiritual Root: {root.get('display_name', '-')}")
        self._p(f"    Essence x{root.get('essence_cultivation_multiplier', '?')} | "
                f"Comprehension x{root.get('comprehension_multiplier', '?')} | "
                f"Breakthrough {root.get('essence_breakthrough_modifier', 0)}")
        self._p(f"  Physique      : {physique.get('display_name', '-')}")
        self._p(f"    Body x{physique.get('body_cultivation_multiplier', '?')} | "
                f"Stat gain x{physique.get('body_stat_gain_multiplier', '?')} | "
                f"Breakthrough {physique.get('body_breakthrough_modifier', 0)}")
        if result.get("event") == EventType.STARTING_FATE_ROLLED:
            self._p("Type 'accept fate' to begin.")
        self._hr()

    def _fmt_character_encounter(self, result: Dict[str, Any]) -> None:
        self._hr()
        self._p(result.get("player_message", "You encounter familiar cultivators nearby."))
        for character in result.get("characters", []):
            options = ", ".join(
                f"{option.get('label')} {option.get('character_id')}"
                for option in character.get("options", [])
            )
            self._p(f"  - {character.get('name', character.get('id'))} [{character.get('relationship_tier', '-')}] {options}")
        self._hr()

    def _fmt_character_interaction(self, result: Dict[str, Any]) -> None:
        self._hr()
        self._p(f"{result.get('name', result.get('character_id', 'Someone'))}:")
        self._p(result.get("player_message", "They acknowledge you."))
        self._hr()

    def _fmt_sects(self, result: Dict[str, Any]) -> None:
        sect = result.get("sect")
        if not sect:
            self._p("No sect is available at this location.")
            return
        self._hr()
        self._p(f"{sect.get('display_name')} (path: {sect.get('path')})")
        self._p(sect.get("description", ""))
        status = sect.get("join_status", {})
        if status.get("allowed"):
            self._p(f"  Join with: join {sect.get('id')}")
        else:
            self._p(f"  Cannot join yet: {status.get('reason', 'requirements not met')}")
        self._hr()

    def _fmt_sect_joined(self, result: Dict[str, Any]) -> None:
        self._p(result.get("player_message", f"You join the sect and take up the path of {result.get('path')}."))

    def _fmt_map(self, result: Dict[str, Any]) -> None:
        self._hr()
        self._p(f"You are at {result.get('location_name', '?')}.")
        position = result.get("map_position", {})
        if isinstance(position, dict) and "x" in position and "y" in position:
            self._p(f"  Map position: ({position['x']:.2f}, {position['y']:.2f})")
        destinations = result.get("destinations", [])
        if destinations:
            self._p("  Reachable:")
            for dest in destinations:
                if dest.get("reachable"):
                    self._p(f"    - {dest.get('display_name', dest.get('id'))} [{dest.get('danger', '?')}]")
                else:
                    self._p(f"    - {dest.get('display_name', dest.get('id'))} (locked: {dest.get('reason', 'unknown')})")
        else:
            self._p("  Nowhere to travel from here.")
        self._hr()

    def _fmt_boon(self, result: Dict[str, Any]) -> None:
        self._p(result.get("player_message", "You receive a gift."))
        reward = result.get("reward", {})
        if reward.get("gold"):
            self._p(f"  Gold +{reward['gold']}.")
        if reward.get("exp"):
            self._p(f"  EXP +{reward['exp']}.")
        for item_id, count in reward.get("items", {}).items():
            self._p(f"  {item_id} x{count}.")
        if reward.get("skill_id"):
            self._p(f"  Learned technique: {reward['skill_id']}.")

    def _fmt_died(self, result: Dict[str, Any]) -> None:
        self._hr()
        self._p(result.get("player_message", "Your lifespan is exhausted."))
        self._p(f"You perished at the age of {result.get('age_years', '?')}. Your journey is over.")
        self._hr()

    def _fmt_help(self, _result: Dict[str, Any]) -> None:
        self._hr()
        self._p("Available commands:")
        for entry in self._router.describe_commands():
            alias = f"  (aliases: {entry['aliases']})" if entry["aliases"] else ""
            self._p(f"  {entry['command']:<18} {entry['desc']}{alias}")
        self._hr()

    def _fmt_error(self, result: Dict[str, Any]) -> None:
        self._p("! " + self._describe_error(result))

    def _fmt_quit(self, _result: Dict[str, Any]) -> None:
        self._p("You sever your ties to the world of cultivation. Until next time.")

    def _fmt_generic(self, result: Dict[str, Any]) -> None:
        message = result.get("message") or result.get("text")
        if message:
            self._p(str(message))

    # -- text helpers -----------------------------------------------------
    def _describe_turn_event(self, event: Dict[str, Any]) -> str:
        action = event.get("action")
        actor = event.get("actor")
        if action == "ATTACK" and actor == "PLAYER":
            return f"You strike for {event.get('damage')} damage."
        if action == "ATTACK" and actor == "ENEMY":
            return f"The {event.get('enemy_name', 'enemy')} hits you for {event.get('damage')} damage."
        if action == "SKILL":
            if "damage" in event:
                return f"You unleash {event.get('skill')} for {event.get('damage')} damage!"
            return f"You channel {event.get('skill')}, but it has no effect here."
        if action == "USE_ITEM":
            bits = [f"You use {event.get('item')}."]
            if event.get("healed"):
                bits.append(f"(+{event['healed']} HP)")
            if event.get("qi_restored"):
                bits.append(f"(+{event['qi_restored']} Qi)")
            return " ".join(bits)
        if action == "FLEE_FAILED":
            return "You try to flee but fail to break away!"
        if action == "FLEE_SUCCESS":
            return "You slip away into the wilderness."
        return str(event)

    def _describe_error(self, result: Dict[str, Any]) -> str:
        reason = result.get("reason")
        messages = {
            "UNKNOWN_COMMAND": lambda: f"Unknown command: '{result.get('input', '')}'. Type 'help'.",
            "NOT_IN_COMBAT": lambda: "There is no enemy here to fight.",
            "INVALID_IN_COMBAT": lambda: "You cannot do that mid-battle. Try: attack, skill, use, flee.",
            "SKILL_ONLY_IN_COMBAT": lambda: "Active skills can only be used in combat.",
            "NO_SKILL_SPECIFIED": lambda: "Specify a skill, e.g. 'skill iron_fist'.",
            "SKILL_NOT_KNOWN": lambda: f"You have not learned '{result.get('skill_id')}'.",
            "SKILL_NOT_USABLE": lambda: f"'{result.get('skill_id')}' cannot be actively used.",
            "SKILL_ON_COOLDOWN": lambda: f"That skill is recovering ({result.get('remaining')} turn(s) left).",
            "NOT_ENOUGH_QI": lambda: f"Not enough Qi (need {result.get('required')}, have {result.get('qi')}).",
            "NO_ITEM_SPECIFIED": lambda: "Specify an item, e.g. 'use healing_pill'.",
            "ITEM_NOT_OWNED": lambda: f"You do not have '{result.get('item_id')}'.",
            "UNKNOWN_ITEM": lambda: f"No such item: '{result.get('item_id')}'.",
            "ITEM_NOT_EQUIPPABLE": lambda: f"'{result.get('item_id')}' cannot be equipped.",
            "INVALID_EQUIPMENT_SLOT": lambda: f"'{result.get('slot')}' is not a valid equipment slot.",
            "SLOT_NOT_ALLOWED": lambda: f"'{result.get('item_id')}' cannot be equipped in '{result.get('slot')}'.",
            "EQUIPMENT_SLOT_EMPTY": lambda: f"Nothing is equipped in '{result.get('slot')}'.",
            "REALM_TOO_LOW": lambda: f"Your realm is too low for that item (requires {result.get('required')}).",
            "STRENGTH_TOO_LOW": lambda: f"Your body strength is too low (requires {result.get('required')}).",
            "COMPREHENSION_TOO_LOW": lambda: f"Your comprehension is too low (requires {result.get('required')}).",
            "REQUIREMENT_NOT_MET": lambda: f"You do not meet this item's requirements ({result.get('required')}).",
            "FATE_NOT_ACCEPTED": lambda: "Your starting fate has not been accepted. Type 'roll fate', then 'accept fate'.",
            "FATE_ALREADY_ACCEPTED": lambda: "Your starting fate has already been accepted.",
            "NO_CHARACTER_SPECIFIED": lambda: "Specify a character id, e.g. 'talk zhu_yan'.",
            "UNKNOWN_CHARACTER": lambda: f"No such character here: '{result.get('character_id')}'.",
            "NO_CHARACTER_ENEMY": lambda: "That character has no combat entry yet.",
            "UNKNOWN_ENEMY": lambda: "That character's combat entry is missing.",
            "NOT_AVAILABLE": lambda: "That interaction is not available.",
            "LOCKED": lambda: "That interaction is not unlocked yet.",
            "RELATIONSHIP_TOO_LOW": lambda: "Your relationship with them is not close enough yet.",
            "MORALITY_BAND_MISMATCH": lambda: "Your alignment does not permit that interaction.",
            "NO_REWARD_AVAILABLE": lambda: "That character has no reward to offer you right now.",
        }
        builder = messages.get(reason)
        return builder() if builder else f"Something went wrong ({reason})."

    # -- prompt / chrome --------------------------------------------------
    def _build_prompt(self) -> str:
        state = self._engine.get_game_state()
        player = state["player"]
        if state.get("awaiting_fate_acceptance"):
            return "\n[Starting Fate pending - type 'roll fate' or 'accept fate']\n> "
        if state["in_combat"] and state["enemy"]:
            enemy = state["enemy"]
            return (f"\n[COMBAT] You {player['hp']}/{player['max_hp']} HP | "
                    f"{enemy['name']} {enemy['hp']}/{enemy['max_hp']} HP\n> ")
        cultivation = player.get("cultivation_state", {})
        body = cultivation.get("body_transformation", {})
        essence = cultivation.get("essence_gathering", {})
        return (f"\n[Body {body.get('display_name', player.get('realm', '-'))} {body.get('progress', player['progress'])}% | "
            f"Essence {essence.get('display_name', player.get('essence_cultivation', '-'))} {essence.get('progress', 0)}% | "
            f"HP {player['hp']}/{player['max_hp']} | Qi {player['qi']}/{player['max_qi']}]\n> ")

    def _print_banner(self) -> None:
        self._p("=" * 60)
        self._p("            M A R T I A L   P A T H")
        self._p("        A Cultivation Text RPG (CLI edition)")
        self._p("=" * 60)
        self._p("Train, explore, fight, loot, and break through the heavens.")

    def _hr(self) -> None:
        self._p("-" * 60)

    def _p(self, text: str = "") -> None:
        """The single output primitive for the whole application."""
        print(text)
