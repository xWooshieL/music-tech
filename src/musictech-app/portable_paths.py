"""Compatibility shim — see :mod:`musictech.utils.portable_paths`.

Note: ``PROJECT_ROOT`` is re-computed locally (instead of imported)
because some legacy callers compare it with paths derived from
``__file__``. We override ``musictech.utils.portable_paths.PROJECT_ROOT``
in place so both views agree on the same value.
"""

from pathlib import Path

import musictech.utils.portable_paths as _impl

PROJECT_ROOT = Path(__file__).resolve().parent
_impl.PROJECT_ROOT = PROJECT_ROOT

from musictech.utils.portable_paths import (  # noqa: E402
    portable_command,
    project_relative_path,
    resolve_project_path,
)

__all__ = [
    "PROJECT_ROOT",
    "portable_command",
    "project_relative_path",
    "resolve_project_path",
]
