"""Compatibility shim — see :mod:`musictech.cli.main_legacy`."""

from musictech.cli.main_legacy import (
    available_input_ports,
    build_parser,
    format_prediction,
    looks_like_midi_path,
    main,
    resolve_score_path,
    run_tracker,
    validate_args,
)

__all__ = [
    "available_input_ports",
    "build_parser",
    "format_prediction",
    "looks_like_midi_path",
    "main",
    "resolve_score_path",
    "run_tracker",
    "validate_args",
]


if __name__ == "__main__":
    raise SystemExit(main())
