"""Evaluation metrics for score followers and tempo agents.

Today the metrics live inside ``autoplay_offset_benchmark.py`` mixed with
the autoplay simulator and CLI parsing. This makes them hard to reuse on
real recordings (ASAP) and on the RL agent.

This sub-package separates *metrics* (pure functions on labeled traces)
from *runners* (batch evaluation over a dataset) and ``CLI``.

Modules planned here:

- ``follower_metrics.py`` — alignment accuracy, onset-error @ 50 / 100 /
                            250 ms, recovery latency, steady-tempo std.
- ``tempo_metrics.py``    — RMS render-perf delay, tempo jerk
                            (``mean (a_t − a_{t-1})²``), tracker
                            disagreement ``L_align``.
- ``runners.py``          — ``evaluate_follower_on_dataset(factory,
                            dataset) -> Report``.
- ``report.py``           — Report DTO + JSON / CSV serialization.

Inputs are typed via :mod:`musictech.core.dto`. Metric functions must be
pure and side-effect free so they can be unit-tested without an audio
stack.
"""

__all__: list[str] = []
