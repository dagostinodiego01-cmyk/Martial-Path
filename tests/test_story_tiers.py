"""Story-tier progression: location tiers, player progress, sect + encounter gating."""
from game.data.registry import GameDataRegistry
from game.models.player import Player
from game.services.character_service import CharacterService
from game.systems.location_system import LocationSystem
from game.systems.morality_system import MoralitySystem
from game.systems.relationship_system import RelationshipSystem


REGISTRY = GameDataRegistry.load()
LOCATIONS = LocationSystem(REGISTRY.locations)
MORALITY = MoralitySystem(REGISTRY.morality)
RELATIONSHIPS = RelationshipSystem(REGISTRY.relationships)


def _characters() -> CharacterService:
    return CharacterService(REGISTRY.characters, LOCATIONS, MORALITY, RELATIONSHIPS)


def _player(location: str, max_story_tier: int) -> Player:
    player = Player(name="Tester", current_location=location)
    player.max_story_tier = max_story_tier
    return player


def test_every_location_has_a_story_tier():
    for location in REGISTRY.locations:
        assert isinstance(location.get("story_tier"), int), f"{location['id']} missing story_tier"
        assert 1 <= location["story_tier"] <= 6, f"{location['id']} story_tier out of range"


def test_story_tier_ascends_from_start_to_endgame():
    assert LOCATIONS.story_tier("outer_forest") == 1
    assert LOCATIONS.story_tier("lin_academy") == 2
    assert LOCATIONS.story_tier("seven_profound_valleys_inner") == 3
    assert LOCATIONS.story_tier("divine_phoenix_island") == 4
    assert LOCATIONS.story_tier("asura_divine_kingdom") == 5
    assert LOCATIONS.story_tier("holy_demon_continent") == 6
    assert LOCATIONS.story_tier("nowhere") == 0


def test_every_sect_has_a_tier_within_1_to_6():
    for sect in REGISTRY.sects:
        tier = sect.get("tier")
        assert isinstance(tier, int) and 1 <= tier <= 6, f"sect {sect['id']} tier {tier}"


def test_higher_tier_sects_live_at_matching_or_higher_story_tiers():
    for sect in REGISTRY.sects:
        tier = sect["tier"]
        for location_id in sect.get("location_ids", []):
            story = LOCATIONS.story_tier(location_id)
            assert story >= tier, f"sect {sect['id']} (tier {tier}) sits at story tier {story}"


def test_character_service_hides_characters_below_their_min_story_tier():
    service = _characters()

    early = service.get_available_characters("asura_divine_kingdom", _player("asura_divine_kingdom", 2))
    assert all(c["id"] != "situ_haotian" for c in early)

    late = service.get_available_characters("asura_divine_kingdom", _player("asura_divine_kingdom", 5))
    assert any(c["id"] == "situ_haotian" for c in late)


def test_character_service_still_shows_untagged_characters():
    service = _characters()

    briefs = service.get_available_characters("starting_village", _player("starting_village", 1))
    assert any(c["id"] == "lin_xiaodong" for c in briefs)
