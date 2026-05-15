"""Hybrid-follower calibration and stress testing.

The four big calibration scripts (``calibrate_hybrid_profile.py``,
``autoplay_offset_benchmark.py``, ``stress_test_hybrid.py``,
``playback_validator.py``) still live in the project root. They each
mix CLI parsing, multiprocessing, file I/O, and the actual fitness
loop, so a clean split is not free. This package is the future home
for the *library* parts (metric functions, scenario builders); the
CLI wrappers will become thin shims pointing here.
"""

__all__: list[str] = []
