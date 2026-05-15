"""MusicTech: realtime score following + RL tempo agent.

The package is the canonical home of every non-GUI module in the
repository. Historical root-level scripts (``hmm_follower.py``,
``output_dispatcher.py``, etc.) survive as **thin shims** that
re-export from ``musictech.*`` so legacy callers (GUI, calibration
CLIs) keep working.

Layer overview (see :doc:`ARCHITECTURE.md` for the full map):

- :mod:`musictech.utils`        — dependency-free helpers.
- :mod:`musictech.core`         — pure-numpy followers and DTOs.
- :mod:`musictech.io`           — MIDI input (live + emulator).
- :mod:`musictech.audio`        — microphone input (placeholder).
- :mod:`musictech.preprocessing` — MIDI → score.json conversion.
- :mod:`musictech.playback`     — tempo tracker, event dispatcher,
                                  orchestra renderers.
- :mod:`musictech.datasets`     — synthetic + future ASAP / MAESTRO.
- :mod:`musictech.evaluation`   — follower / tempo metrics (placeholder).
- :mod:`musictech.calibration`  — hybrid profile calibrators (placeholder).
- :mod:`musictech.pipelines`    — high-level import / training scenarios.
- :mod:`musictech.validation`   — interactive validation harnesses.
- :mod:`musictech.rl`           — Gymnasium env + policy skeleton.
- :mod:`musictech.cli`          — CLI entry points.
- :mod:`musictech.gui`          — GUI placeholder (legacy GUI stays
                                  at root for now).

Constraints on new code (enforced informally):

- Pure-numpy hot path for followers and tempo updates.
- DTOs in :mod:`musictech.core.dto` are the only contract between
  layers — do not import ``hybrid_fusion`` from the RL agent.
- Large legacy files (``interactive_tester.py``, ``midi_workspace.py``,
  ``midi/real_orchestra_player.py``) are **not** to be touched
  without an explicit migration plan; they have hundreds of cross-
  imports.
"""

__all__ = [
    "audio",
    "calibration",
    "cli",
    "core",
    "datasets",
    "evaluation",
    "gui",
    "io",
    "pipelines",
    "playback",
    "preprocessing",
    "rl",
    "utils",
    "validation",
]
