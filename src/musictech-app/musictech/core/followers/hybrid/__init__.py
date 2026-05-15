"""Hybrid HSMM + OLTW follower with anchor-window recovery.

The hybrid follower is the "classical tracker" referenced in the
conference theses (``papers/тезисы.pdf``). It composes
:class:`ScoreFollowerHSMM` and :class:`ScoreFollowerOLTW`: the HSMM
runs as the primary tracker, the OLTW provides a fallback when HSMM
confidence drops, and an anchor-window search recovers from gross
desynchronizations (skips, repeats, missed entries).

This sub-package splits the original ~870-line ``hybrid_fusion.py``
into two roles:

- :mod:`.profile` — JSON-based tuning profile (one per piece). Pure
  functions, no follower state. Independent of numpy.
- :mod:`.hybrid` — the :class:`HybridScoreFollower` class itself
  (state, ``process_event``, anchor recovery, debouncer).

A finer split into ``anchor.py`` / ``debounce.py`` is deliberately
postponed: those algorithms read and mutate a lot of follower state,
so cutting them out would require either mixins or threading the
state through long parameter lists. Both options reduce clarity
without reducing total complexity. They will be revisited if/when the
anchor search is replaced by a learned model.
"""

from .hybrid import HybridScoreFollower
from .profile import (
    HYBRID_PROFILE_FORMAT_VERSION,
    HYBRID_PROFILE_TUNING_KEYS,
    hybrid_profile_path,
    load_hybrid_profile,
)

__all__ = [
    "HYBRID_PROFILE_FORMAT_VERSION",
    "HYBRID_PROFILE_TUNING_KEYS",
    "HybridScoreFollower",
    "hybrid_profile_path",
    "load_hybrid_profile",
]
