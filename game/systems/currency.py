"""Shared currency helpers.

Purchases (shops) and technique tuition (trainers) both spend the same two
currencies: Gold (``player.gold``) and Spirit Stones (an inventory item). These
small, pure helpers keep the spend/affordability rules in one place so both
systems behave identically. They never format player-facing text.
"""
from __future__ import annotations

from typing import Any, Dict

from game.models.player import Player

#: Currencies the economy understands. Gold lives on the player; every other
#: supported currency is a stackable inventory item counted by its item id.
SUPPORTED_CURRENCIES = {"gold", "spirit_stone"}


def normalise_price(price: Dict[str, Any] | None) -> Dict[str, int]:
    """Return only the supported, positive currency amounts from a raw price."""
    price = price or {}
    return {
        str(currency): int(amount)
        for currency, amount in price.items()
        if currency in SUPPORTED_CURRENCIES and int(amount) > 0
    }


def currency_amount(player: Player, currency: str) -> int:
    """Return how much of ``currency`` the player currently holds."""
    if currency == "gold":
        return int(player.gold)
    return int(player.inventory.get(currency, 0))


def shortage(player: Player, price: Dict[str, int]) -> Dict[str, int]:
    """Return the missing amount per currency the player cannot afford."""
    missing: Dict[str, int] = {}
    for currency, required in price.items():
        available = currency_amount(player, currency)
        if available < required:
            missing[currency] = required - available
    return missing


def spend(player: Player, price: Dict[str, int]) -> None:
    """Deduct an affordable ``price`` from the player's wallet/inventory."""
    for currency, amount in price.items():
        if currency == "gold":
            player.gold -= amount
        else:
            remaining = player.inventory.get(currency, 0) - amount
            if remaining > 0:
                player.inventory[currency] = remaining
            else:
                player.inventory.pop(currency, None)


def wallet_view(player: Player) -> Dict[str, int]:
    """Return a UI-safe snapshot of the player's spendable currencies."""
    return {"gold": int(player.gold), "spirit_stone": int(player.inventory.get("spirit_stone", 0))}
