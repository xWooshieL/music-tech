"""Offline MIDI parser: list every ``note_on`` with its absolute timestamp.

Used by the dispatcher smoke test and the calibration benchmarks. For
realtime replay see :class:`MidiEmulator`.
"""

from __future__ import annotations

from pathlib import Path

from ._helpers import _require_mido

__all__ = ["iter_midi_note_events"]


def iter_midi_note_events(midi_path: str | Path) -> list[dict[str, float | int]]:
    """Return ``[{pitch, timestamp}, ...]`` for every ``note_on`` in ``midi_path``."""
    midi_lib = _require_mido()
    midi_file = midi_lib.MidiFile(Path(midi_path))
    elapsed = 0.0
    events: list[dict[str, float | int]] = []

    for message in midi_file:
        elapsed += float(getattr(message, "time", 0.0))
        if (
            getattr(message, "type", None) == "note_on"
            and int(getattr(message, "velocity", 0)) > 0
        ):
            events.append(
                {
                    "pitch": int(message.note),
                    "timestamp": elapsed,
                }
            )

    return events
