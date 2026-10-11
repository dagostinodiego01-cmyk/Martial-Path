"""Pytest configuration.

An (otherwise empty) ``conftest.py`` at the repository root ensures pytest adds
this directory to ``sys.path`` during collection, so tests can ``import game``
and its subpackages regardless of the working directory.

It also points ``MARTIAL_PATH_SAVE_DIR`` at a shared temporary directory before
any test runs. ``SaveRepository`` honours that override for its default save
location, so tests that exercise the default-path code path (autosave, API
smoke, engine saves that never inject a ``tmp_path``) never write into the
real ``%APPDATA%``/``~`` save directory.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

os.environ.setdefault(
    "MARTIAL_PATH_SAVE_DIR",
    str(Path(tempfile.gettempdir()) / "martial_path_pytest_saves"),
)
