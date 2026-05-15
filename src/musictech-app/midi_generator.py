"""Compatibility shim — see :mod:`musictech.datasets.synthetic`."""

from musictech.datasets.synthetic import (
    DEFAULT_OUTPUT_DIR,
    DEFAULT_TEMPO,
    DEFAULT_TICKS_PER_BEAT,
    ScaleEvent,
    build_score,
    generate_dataset,
    ideal_case,
    main,
    noisy_case,
    polyphonic_case,
    rubato_case,
    save_pair,
    seconds_to_ticks,
    write_midi,
)

__all__ = [
    "DEFAULT_OUTPUT_DIR",
    "DEFAULT_TEMPO",
    "DEFAULT_TICKS_PER_BEAT",
    "ScaleEvent",
    "build_score",
    "generate_dataset",
    "ideal_case",
    "main",
    "noisy_case",
    "polyphonic_case",
    "rubato_case",
    "save_pair",
    "seconds_to_ticks",
    "write_midi",
]


if __name__ == "__main__":
    main()
