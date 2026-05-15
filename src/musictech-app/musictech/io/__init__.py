"""I/O layer: MIDI input (live and file-based replay).

This layer owns the producer side of the realtime pipeline: a thread
that pushes ``PerformanceEvent``-shaped dicts onto a queue. The
consumer (follower → dispatcher → orchestra) does not care whether
the source is a hardware MIDI port, a MIDI file replay, or a future
microphone+onset detector.

Modules:

- :mod:`musictech.io.midi` — ``LiveMidiReceiver`` (port) and
  ``MidiEmulator`` (file replay).
- :mod:`musictech.audio` — microphone capture. Currently empty;
  exists as the placeholder for the customer's microphone requirement.
"""

__all__: list[str] = []
