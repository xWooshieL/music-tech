"""High-level pipelines composing preprocessing, calibration, and import.

The actual pipeline scripts (``midi_workspace.py``,
``prepare_study_mode_batch.py``) still live in the project root.
They each contain ~500-800 lines of subprocess plumbing, unicode
normalization, and CLI parsing that does not belong in a library
module. Splitting them is a follow-up refactor.

For now, this package is a placeholder so new pipelines (e.g.
``rl_training.py``, ``asap_importer.py``) have a clear home.
"""

__all__: list[str] = []
