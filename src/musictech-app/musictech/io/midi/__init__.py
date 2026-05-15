"""MIDI input: live port listener and file-based emulator.

The two producers share the same wire format
(``{"pitch": int, "timestamp": float}``) and the same queue API, so a
single consumer can switch from real hardware to file replay just by
swapping the source object.

Modules:

- :mod:`._helpers`   — internal queue / mido helpers (``_drain_queue``,
                       ``_push_event``).
- :mod:`.receiver`   — :class:`LiveMidiReceiver` (hardware port).
- :mod:`.emulator`   — :class:`MidiEmulator` (file replay in realtime).
- :mod:`.parser`     — :func:`iter_midi_note_events` (offline reader,
                       used by the dispatcher demo and benchmarks).
"""

from ._helpers import MidiEvent, MidiEventQueue
from .emulator import MidiEmulator
from .parser import iter_midi_note_events
from .receiver import LiveMidiReceiver

__all__ = [
    "LiveMidiReceiver",
    "MidiEmulator",
    "MidiEvent",
    "MidiEventQueue",
    "iter_midi_note_events",
]
