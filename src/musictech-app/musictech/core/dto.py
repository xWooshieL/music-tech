"""Typed data transfer objects (DTOs) shared between layers.

The existing codebase passes data as ``dict[str, Any]`` and positional
tuples, which makes the architecture hard to follow. This module gives
new code explicit types for the three main object families:

1. Static score data (``ScoreNote``, ``TempoMarker``, ``ScoreDocument``).
2. Realtime performer events (``PerformanceEvent``).
3. Follower outputs and tempo state (``AlphaSummary``, ``FollowerOutput``,
   ``TempoEstimate``).
4. RL interface (``RLObservation``, ``RLAction``, ``RLReward``).

All DTOs are deliberately minimal: pure-Python dataclasses / TypedDicts,
no third-party dependencies. They are *contracts*, not behavior — methods
should live in the modules that consume them.

Compatibility helpers (``to_performance_event``, ``from_score_note_dict``)
let new code interoperate with legacy ``dict`` payloads without rewriting
``hybrid_fusion`` / ``output_dispatcher``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Sequence, TypedDict

import numpy as np


# ---------------------------------------------------------------------------
# Static score data
# ---------------------------------------------------------------------------


class ScoreNote(TypedDict, total=False):
    """One state in the score JSON. Either ``pitch`` (legacy) or ``pitches``."""

    index: int
    pitch: int
    pitches: list[int]
    nominal_onset: float
    nominal_duration: float


class TempoMarker(TypedDict):
    """A tempo annotation extracted from the source MIDI."""

    onset: float
    bpm: float


class ScoreDocument(TypedDict, total=False):
    """The top-level score JSON object loaded from ``score.json``."""

    piece_name: str
    notes: list[ScoreNote]
    bar_to_index: dict[int, int]
    tempo_map: list[TempoMarker]


def from_score_note_dict(note: dict[str, Any]) -> ScoreNote:
    """Normalize a raw JSON dict into a ``ScoreNote``.

    Accepts both legacy (``pitch: int``) and chord (``pitches: list[int]``)
    formats and never invents missing fields.
    """
    result: ScoreNote = {"index": int(note["index"])}
    if "pitches" in note:
        result["pitches"] = [int(p) for p in note["pitches"]]
    if "pitch" in note:
        result["pitch"] = int(note["pitch"])
    if "nominal_onset" in note:
        result["nominal_onset"] = float(note["nominal_onset"])
    if "nominal_duration" in note:
        result["nominal_duration"] = float(note["nominal_duration"])
    return result


# ---------------------------------------------------------------------------
# Realtime performer events
# ---------------------------------------------------------------------------


class PerformanceEvent(TypedDict, total=False):
    """One MIDI ``note_on`` (or microphone-derived equivalent).

    ``pitch`` is the dominant note; ``chroma`` is the optional 12-vector
    used when the input comes from audio rather than MIDI.
    """

    pitch: int
    timestamp: float
    velocity: int
    chroma: np.ndarray


def to_performance_event(payload: dict[str, Any]) -> PerformanceEvent:
    """Convert the legacy ``{pitch, timestamp}`` dict into ``PerformanceEvent``."""
    event: PerformanceEvent = {
        "pitch": int(payload["pitch"]),
        "timestamp": float(payload["timestamp"]),
    }
    if "velocity" in payload:
        event["velocity"] = int(payload["velocity"])
    if "chroma" in payload:
        event["chroma"] = np.asarray(payload["chroma"], dtype=np.float64)
    return event


# ---------------------------------------------------------------------------
# Follower output and tempo state
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AlphaSummary:
    """Compressed posterior of the follower over score positions.

    This is the ``α̂_t`` from the thesis: instead of feeding the full
    N-dimensional distribution to the RL agent, we summarize it with a few
    scalars that do not depend on the piece length.
    """

    max_value: float
    entropy: float
    argmax_normalized: float
    top3_indices: tuple[int, int, int]
    top3_mass: float


@dataclass(frozen=True)
class FollowerOutput:
    """Result of one follower step.

    ``model_label`` is useful for diagnostics when the hybrid follower
    switches between HSMM and OLTW.
    """

    score_index: int
    alpha_summary: AlphaSummary
    confidence: float
    model_label: str
    timestamp: float
    resynced: bool = False


@dataclass(frozen=True)
class TempoEstimate:
    """Output of ``TempoTracker.update`` plus its history window."""

    ratio: float
    confidence: float
    history: tuple[float, ...]
    variance: float


# ---------------------------------------------------------------------------
# RL interface (thesis equation 1)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RLObservation:
    """``s_t`` from the thesis.

    ``tempo_history`` and ``emission_error_history`` are fixed-length windows
    of the K most recent values. Shape: ``(K,)``.
    """

    alpha: AlphaSummary
    tempo_history: np.ndarray
    emission_error_history: np.ndarray
    score_position_normalized: float

    def as_vector(self) -> np.ndarray:
        """Flatten to a single numpy vector for MLP input."""
        return np.concatenate(
            (
                np.asarray(
                    [
                        self.alpha.max_value,
                        self.alpha.entropy,
                        self.alpha.argmax_normalized,
                        self.alpha.top3_mass,
                        float(self.alpha.top3_indices[0]),
                        float(self.alpha.top3_indices[1]),
                        float(self.alpha.top3_indices[2]),
                        self.score_position_normalized,
                    ],
                    dtype=np.float64,
                ),
                np.asarray(self.tempo_history, dtype=np.float64),
                np.asarray(self.emission_error_history, dtype=np.float64),
            )
        )


@dataclass(frozen=True)
class RLAction:
    """``a_t`` from the thesis, the tempo coefficient."""

    tempo_coefficient: float


@dataclass(frozen=True)
class RLReward:
    """``r_t`` from the thesis, broken into diagnostic components.

    ``total == sync_error + alignment_error + tempo_jerk``.
    """

    total: float
    sync_error: float
    alignment_error: float
    tempo_jerk: float


__all__ = [
    "AlphaSummary",
    "FollowerOutput",
    "PerformanceEvent",
    "RLAction",
    "RLObservation",
    "RLReward",
    "ScoreDocument",
    "ScoreNote",
    "TempoEstimate",
    "TempoMarker",
    "from_score_note_dict",
    "to_performance_event",
]
