"""Compatibility shim. The two classes are now in separate modules:

- :class:`musictech.io.midi.receiver.LiveMidiReceiver`
- :class:`musictech.io.midi.emulator.MidiEmulator`

The module also re-exports the ``mido`` handle that ``main.py``
imports as ``from live_midi_receiver import ..., mido as live_mido``.
"""

from musictech.io.midi._helpers import (
    MidiEvent,
    MidiEventQueue,
    _drain_queue,
    _push_event,
    mido,
)
from musictech.io.midi.emulator import MidiEmulator
from musictech.io.midi.receiver import LiveMidiReceiver

__all__ = [
    "LiveMidiReceiver",
    "MidiEmulator",
    "MidiEvent",
    "MidiEventQueue",
    "_drain_queue",
    "_push_event",
    "mido",
]
