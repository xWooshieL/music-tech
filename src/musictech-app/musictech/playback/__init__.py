"""Realtime playback layer: tempo tracking and orchestral rendering.

This layer consumes follower predictions (a stream of
``(score_index, timestamp)`` pairs) and produces audible output.

Module structure:

- :mod:`.score_loader` — shared score-JSON loader used by every
  component below. Lives here (and not in
  :mod:`musictech.core.followers`) because it does not need numpy and
  belongs to the I/O layer.
- :mod:`.events` — dataclasses passed between the tracker and the
  dispatcher (``TempoObservation``, ``DispatchEvent``).
- :mod:`.tempo_tracker` — :class:`TempoTracker`, the rolling-window
  tempo estimator (median over the last ``history_size``
  observations).
- :mod:`.event_dispatcher` — :class:`ScoreEventDispatcher`, the
  worker-thread fan-out that calls subscriber callbacks.
- :mod:`.orchestra.mock` — :class:`MockOrchestraPlayer`, console-only
  stub for integration tests.
- :mod:`.orchestra.pygame_midi` — :class:`PygameMidiOrchestra`,
  simple chord renderer over ``pygame.midi``.

The richer :class:`DynamicOrchestraPlayer` (Philharmonia samples,
expression / CC routing) still lives at
``midi/real_orchestra_player.py``. It is large, self-contained, and
not refactored here.
"""

from .event_dispatcher import ScoreEventDispatcher
from .events import DispatchCallback, DispatchEvent, TempoObservation
from .orchestra.mock import MockOrchestraPlayer
from .orchestra.pygame_midi import PygameMidiOrchestra
from .tempo_tracker import TempoTracker

__all__ = [
    "DispatchCallback",
    "DispatchEvent",
    "MockOrchestraPlayer",
    "PygameMidiOrchestra",
    "ScoreEventDispatcher",
    "TempoObservation",
    "TempoTracker",
]
