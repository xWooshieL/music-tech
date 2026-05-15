"""Core ML layer: score followers and DTOs.

The four score followers and the typed DTOs all live inside
:mod:`musictech.core.followers` and :mod:`musictech.core.dto`. They
are pure-numpy state machines with no I/O dependencies (no ``mido``,
no ``pygame``), suitable for use from the RL environment, evaluation
harnesses, and headless tests.

Constraints for code added to this layer:

- pure numpy, no ``mido``, no ``pygame``;
- no blocking I/O in the realtime hot path (``process_event``,
  ``update``);
- public API of existing followers must not change — many callers
  depend on it.

Future work that belongs here:

- An improved HSMM with explicit duration distributions (Cont 2010).
- Beam-search forward to keep latency under 20 ms for large scores.
- Structural transitions (repeat / insertion / deletion) à la
  Nakamura 2015.
"""

from . import dto
from .followers import (
    HybridScoreFollower,
    ScoreFollowerHMM,
    ScoreFollowerHSMM,
    ScoreFollowerOLTW,
)

__all__ = [
    "HybridScoreFollower",
    "ScoreFollowerHMM",
    "ScoreFollowerHSMM",
    "ScoreFollowerOLTW",
    "dto",
]
