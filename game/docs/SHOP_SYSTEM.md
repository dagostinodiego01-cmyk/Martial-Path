# Shop System

Martial Path shops are data-driven markets that let the player spend Gold or Spirit Stones on items and equipment.

The authoritative logic lives in `game/systems/shop_system.py`. UI layers only display shop state and send `SHOP` / `BUY_ITEM` actions.

## Data

Shop definitions live in `game/data/shops.json` and are loaded by `GameDataRegistry`.

Each shop has stable IDs, one or more `location_ids`, descriptive text, and a `stock` list. Stock entries reference existing item/equipment IDs and define a `price` object keyed by supported currency:

- `gold`: deducted from `player.gold`.
- `spirit_stone`: deducted from the player's `spirit_stone` inventory count.

Equipment stock should normally use a `stock` value of `1`, which limits a single purchase request to one copy. Consumables can omit `stock` for repeatable purchases.

## Actions

- `SHOP`: returns the first shop available at the player's current location, or the requested `shop_id` if supplied.
- `BUY_ITEM`: validates the current location, stock entry, quantity, and currency, then adds the purchased item to inventory.

Purchasing does not equip items automatically. The player must still use `EQUIP_ITEM`, so all equipment slot and requirement checks remain owned by `EquipmentSystem`.

## Validation

The central data validator checks shop IDs, location references, stock item references, supported currencies, positive prices, and optional stock limits. Broken shop data fails `validate_all_game_data()` and the shipped-data test suite.