"""Dataset importers and synthetic generators.

Modules:

- :mod:`.synthetic` — ``midi_generator.py`` reborn here. Produces the
  4-piece synthetic dataset used by smoke tests.
- ``asap.py``      — ASAP (Foscarin et al. 2020). **Not yet
                     implemented.** Blocks all RL training; write
                     this first if you need real performances paired
                     with scores.
- ``maestro.py``   — MAESTRO v3 (optional augmentation).
- ``manifest.py``  — read/write ``datasets/<corpus>/manifest.json``.

Layout produced by the importers:

    datasets/<corpus>/<piece>/
        score.json                    # our score format
        performances/<perf_id>.json   # list of {score_index, pitch, timestamp}
    datasets/<corpus>/manifest.json
"""

from .synthetic import generate_dataset

__all__ = ["generate_dataset"]
