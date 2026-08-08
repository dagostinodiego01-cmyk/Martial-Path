"""UI layer: the CLI frontend.

This is the ONLY layer permitted to call ``print`` / ``input`` and to format
text for the player. It reads raw input, asks the router to structure it, hands
the command to the engine, then renders whatever structured result comes back.

Because all rendering keys off :class:`~core.constants.EventType` values, this
file can be replaced wholesale (by a web, GUI, or API frontend) without touching
the router, engine, or systems.
"""
