"""Action-dispatch mixins for :class:`~game.core.game_engine.GameEngine`.

``GameEngine`` is one class, but it coordinates nine distinct concerns. Each is a
mixin here so the single orchestrator file stays readable: the mixins hold method
bodies only (no ``__init__``) and read the state that ``GameEngine.__init__``
sets up. They are implementation details — import ``GameEngine`` from
``game.core.game_engine``, never from this package.
"""
