# Equipment System

Martial Path equipment is data-driven and includes ordinary gear plus cultivation treasures such as rings, cloaks, amulets, talismans, artifacts, and flying swords.

The authoritative logic lives in `game/systems/equipment_system.py`. UI layers only display equipment state and send `EQUIP_ITEM` / `UNEQUIP_ITEM` actions.

## Slots

The player has these persistent equipment slots:

- `weapon`
- `armor`
- `boots`
- `cloak`
- `ring_1`
- `ring_2`
- `amulet`
- `talisman`
- `artifact_1`
- `artifact_2`
- `flying_sword`

Rings can use either ring slot. Artifacts can use either artifact slot. Flying swords use only `flying_sword` and do not occupy the normal weapon slot unless data explicitly changes that in the future.

## Data

Equipment definitions live in `game/data/equipment.json` and are also projected into the item registry so inventory ownership and rewards can use normal item IDs.

Each equipment entry defines identity, slot compatibility, category, rarity, requirements, stat modifiers, cultivation modifiers, utility modifiers, tags, value, and equippable metadata.

## Ownership and Equipping

Equipment can enter the player's inventory through loot, quest rewards, or shops. `ShopSystem` handles purchasing from data-driven market stock; `EquipmentSystem` only validates equipping once the item is already owned.

Equipment can only be equipped if the player owns the item in inventory. Equipping keeps the item in inventory and stores its ID in the target equipment slot. Replacing an occupied slot simply changes the slot reference; it does not duplicate or remove inventory items.

Unequipping clears the slot. Equipping and unequipping never mutate base stats.

## Derived Stats

Equipment contributes through derived calculations:

- `StatsSystem.effective_stats()` includes equipment stat modifiers.
- Combat uses effective attack and effective defense.
- `GameEngine.get_game_state()` exposes `equipment`, `equipment_details`, `equipment_modifiers`, and `effective_stats` as read-only state.

Base fields such as `player.attack`, `player.defense`, `player.max_hp`, and `player.max_qi` are not changed by equipment.

## Cultivation Modifiers

Supported V1 cultivation modifiers include:

- `body_cultivation_flat_bonus`
- `essence_cultivation_flat_bonus`
- `body_strain_gain_multiplier`
- `foundation_stability_bonus`
- `breakthrough_chance_modifier`
- `body_breakthrough_modifier`
- `essence_breakthrough_modifier`
- `comprehension_bonus`

Equipment modifiers are intentionally small and mostly flat so they do not overwhelm Martial and Body Talent multipliers.

## Requirements

Equipment requirements may check Body realm, Essence realm, body strength, comprehension, faction, and quest flags. Faction and quest checks are reserved for future state support and currently reject with structured requirement errors when present.

## Follow-Up Work

- Weighted equipment loot tables.
- Sect contribution rewards and dynamic auctions.
- Forging, refinement, durability, socketing, and set bonuses.
- Cursed or soul-bound treasures.
- Artifact spirits, artifact evolution, and binding.
- Flying sword fast travel, aerial combat, and sword intent.
- Storage ring inventory expansion.