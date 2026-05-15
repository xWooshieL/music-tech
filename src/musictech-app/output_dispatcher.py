"""Compatibility shim. The original 682-line monolith is now split into:

- :mod:`musictech.playback.events`            — DTOs.
- :mod:`musictech.playback.score_loader`      — score JSON loader.
- :mod:`musictech.playback.tempo_tracker`     — :class:`TempoTracker`.
- :mod:`musictech.playback.event_dispatcher`  — :class:`ScoreEventDispatcher`.
- :mod:`musictech.playback.orchestra.mock`    — :class:`MockOrchestraPlayer`.
- :mod:`musictech.playback.orchestra.pygame_midi`
                                              — :class:`PygameMidiOrchestra`.
- :mod:`musictech.io.midi.parser`             — :func:`iter_midi_note_events`.

Legacy callers still use module-private symbols (``_load_score``,
``_note_pitches``, ``_require_mido``); those are re-exported below
without an underscore-stripped public name.
"""

from musictech.io.midi._helpers import _require_mido
from musictech.io.midi.parser import iter_midi_note_events
from musictech.playback.event_dispatcher import ScoreEventDispatcher
from musictech.playback.events import DispatchCallback, DispatchEvent, TempoObservation
from musictech.playback.orchestra.mock import MockOrchestraPlayer
from musictech.playback.orchestra.pygame_midi import PygameMidiOrchestra
from musictech.playback.score_loader import (
    load_score as _load_score,
    note_pitches as _note_pitches,
    representative_pitch as _representative_pitch,
)
from musictech.playback.tempo_tracker import TempoTracker

__all__ = [
    "DispatchCallback",
    "DispatchEvent",
    "MockOrchestraPlayer",
    "PygameMidiOrchestra",
    "ScoreEventDispatcher",
    "TempoObservation",
    "TempoTracker",
    "iter_midi_note_events",
]
