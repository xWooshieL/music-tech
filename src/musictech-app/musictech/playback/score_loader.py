"""Lightweight score-JSON loader shared by every playback component.

The followers in :mod:`musictech.core.followers` also load scores, but
they live behind a numpy-heavy API. Here we only need ``notes`` as
plain dicts, so we keep a tiny duplicate that does not pull numpy
just to deserialize JSON.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

__all__ = ["load_score", "note_pitches", "representative_pitch"]


def load_score(
    score_json: str | Path | dict[str, Any] | list[dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Return ``(score_data, notes)`` for any accepted score input.

    Accepts a path, an in-memory ``score_data`` dict, or a bare list of
    notes (which we wrap as ``{"notes": [...]}``). Raises
    ``ValueError`` if the structure is wrong.
    """
    if isinstance(score_json, (str, Path)):
        score_path = Path(score_json)
        if score_path.suffix.lower() in {".mid", ".midi"}:
            raise ValueError("Expected a score JSON file, not a MIDI file.")

        try:
            payload = json.loads(score_path.read_text(encoding="utf-8"))
        except UnicodeDecodeError as exc:
            raise ValueError(f"Could not decode score JSON: {score_path}") from exc
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid score JSON: {score_path}") from exc
    else:
        payload = score_json

    if isinstance(payload, list):
        notes = payload
        score_data = {"notes": notes}
    elif isinstance(payload, dict):
        notes = payload.get("notes")
        score_data = payload
    else:
        raise TypeError("score_json must be a path, a score dict, or a list of notes")

    if not isinstance(notes, list) or not notes:
        raise ValueError("score_json must contain a non-empty top-level list of notes")

    for position, note in enumerate(notes):
        if not isinstance(note, dict):
            raise ValueError(f"score note #{position} must be a JSON object")
        if "pitch" not in note and "pitches" not in note:
            raise ValueError(f"score note #{position} is missing 'pitch'/'pitches'")
        if "nominal_duration" not in note:
            raise ValueError(f"score note #{position} is missing 'nominal_duration'")

    return score_data, notes


def note_pitches(note: dict[str, Any]) -> list[int]:
    """Return the list of integer MIDI pitches for one score note (mono or chord)."""
    raw_pitches = note.get("pitches")
    if raw_pitches is None:
        raw_pitch = note.get("pitch")
        if raw_pitch is None:
            raise ValueError("score note is missing 'pitch'/'pitches'")
        return [int(raw_pitch)]

    if not isinstance(raw_pitches, list) or not raw_pitches:
        raise ValueError("score note 'pitches' must be a non-empty list")
    return [int(pitch) for pitch in raw_pitches]


def representative_pitch(note: dict[str, Any]) -> int:
    """Pick a single representative pitch for ``note`` (max of the chord)."""
    return max(note_pitches(note))
