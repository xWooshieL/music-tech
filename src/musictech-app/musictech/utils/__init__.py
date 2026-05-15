"""Utility helpers used across MusicTech layers.

This layer carries small, dependency-free helpers: a polyfill for
``zip(strict=...)``, project-path normalization. Anything heavier (numpy
helpers, MIDI helpers) belongs to its own layer.
"""

from .compat import compat_zip
from .portable_paths import (
    PROJECT_ROOT,
    portable_command,
    project_relative_path,
    resolve_project_path,
)

__all__ = [
    "PROJECT_ROOT",
    "compat_zip",
    "portable_command",
    "project_relative_path",
    "resolve_project_path",
]
