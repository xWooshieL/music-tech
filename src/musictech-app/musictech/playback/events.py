"""Plain-dataclass DTOs passed inside the playback layer.

These are intentionally separate from :mod:`musictech.core.dto`: that
module describes contracts between *layers* (follower → RL agent →
evaluation), whereas these classes are internal to playback (tempo
tracker → event dispatcher → orchestra player).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

__all__ = ["DispatchCallback", "DispatchEvent", "TempoObservation"]


DispatchCallback = Callable[[int, float], None]


@dataclass(frozen=True)
class TempoObservation:
    """A single tempo measurement derived from two control points."""

    nominal_elapsed: float
    actual_elapsed: float
    raw_ratio: float


@dataclass(frozen=True)
class DispatchEvent:
    """One follower prediction queued for delivery to subscribers."""

    index: int
    timestamp: float
    tempo_update: bool = True
