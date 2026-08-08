"""Systems layer: pure gameplay rules.

Every system in this package obeys the same contract:

* It accepts structured inputs (model objects, ids, an :class:`RNG`).
* It returns structured outputs (result dictionaries tagged with an
  :class:`~core.constants.EventType`).
* It contains ZERO UI logic — no ``print``, no ``input``, no text formatting
  intended for the player.

This is what lets the UI be swapped without touching the rules.
"""
