"""Compatibility shim — see :mod:`musictech.cli.dataset_viewer`."""

from musictech.cli.dataset_viewer import (
    DEFAULT_DATASET_DIR,
    discover_pairs,
    load_performance,
    load_score,
    main,
    render_pair,
)

__all__ = [
    "DEFAULT_DATASET_DIR",
    "discover_pairs",
    "load_performance",
    "load_score",
    "main",
    "render_pair",
]


if __name__ == "__main__":
    main()
