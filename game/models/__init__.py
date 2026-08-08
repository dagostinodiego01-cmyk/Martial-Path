"""Domain models: plain data holders with light, UI-free behaviour.

Models describe *what things are* (a player, an enemy, an item, a skill). They
carry state and trivial state transitions but never contain gameplay rules,
randomness, or I/O. Systems operate on these models to produce results.
"""
