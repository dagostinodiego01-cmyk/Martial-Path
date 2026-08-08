"""Pytest configuration.

An (otherwise empty) ``conftest.py`` at the repository root ensures pytest adds
this directory to ``sys.path`` during collection, so tests can ``import game``
and its subpackages regardless of the working directory.
"""
