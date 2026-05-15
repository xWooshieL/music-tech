"""MIDI preprocessing: MIDI → score.json, hand split, track reduction.

Modules:

- :mod:`.midi_to_score` — ``convert_to_score`` (the main importer).
- :mod:`.hand_splitter` — left/right hand separation by pitch density.
- :mod:`.midi_splitter` — split a MIDI by pitch boundary or by tracks.
- :mod:`.reduce_tracks` — flatten a multi-track MIDI into a single
  performance track.
"""

__all__: list[str] = []
