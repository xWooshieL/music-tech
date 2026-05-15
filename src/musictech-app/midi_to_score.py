"""Compatibility shim — see :mod:`musictech.preprocessing.midi_to_score`."""

from musictech.preprocessing.midi_to_score import (
    NoteEvent,
    build_parser,
    cluster_note_events,
    cluster_onset_time,
    cluster_state_duration,
    convert_to_score,
    extract_note_events,
    main,
    select_cluster_events,
)

__all__ = [
    "NoteEvent",
    "build_parser",
    "cluster_note_events",
    "cluster_onset_time",
    "cluster_state_duration",
    "convert_to_score",
    "extract_note_events",
    "main",
    "select_cluster_events",
]


if __name__ == "__main__":
    raise SystemExit(main())
