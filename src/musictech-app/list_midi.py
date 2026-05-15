"""Compatibility shim — see :mod:`musictech.cli.list_midi`."""

from musictech.cli.list_midi import main

__all__ = ["main"]


if __name__ == "__main__":
    raise SystemExit(main())
