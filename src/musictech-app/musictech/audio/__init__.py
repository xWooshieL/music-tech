"""Audio (microphone) input — customer requirement, not part of the thesis.

The thesis assumes MIDI input (see Fig. 1 in ``papers/тезисы.pdf``). The
customer requirements list, however, says the soloist input may come from
either MIDI **or** a microphone.

This sub-package, when implemented, exposes the same producer API as
``live_midi_receiver.LiveMidiReceiver`` (a thread that pushes
``PerformanceEvent`` into a ``queue.Queue``), so that the rest of the
pipeline does not need to know whether the source is MIDI or audio.

Modules planned here:

- ``capture.py``         — ``MicrophoneCapture`` over ``sounddevice.InputStream``,
                           low-latency (block size ~10 ms).
- ``onset.py``           — spectral-flux onset detector.
- ``chroma_emission.py`` — alternative emission function for the HSMM that
                           accepts a 12-D chroma vector instead of a single
                           MIDI pitch. Plugs into
                           :class:`musictech.core.ScoreFollowerHSMM` via a
                           future emission-function hook.

This layer is **optional** for the thesis-driven plan. The MIDI-only
prototype already satisfies the customer requirement formally
("через микрофон (или MIDI-вход)").

When implemented, the layer must not pull ``torch`` or any GPU dependency.
A CPU pipeline (numpy / scipy / librosa / own STFT) is sufficient.
"""

__all__: list[str] = []
