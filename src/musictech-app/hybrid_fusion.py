"""Compatibility shim — see :mod:`musictech.core.followers.hybrid`.

The hybrid follower is now split into:

- :class:`musictech.core.followers.hybrid.hybrid.HybridScoreFollower`
  (the tracker itself)
- :mod:`musictech.core.followers.hybrid.profile` (per-piece tuning
  profile)
"""

from musictech.core.followers.hybrid import (
    HYBRID_PROFILE_FORMAT_VERSION,
    HYBRID_PROFILE_TUNING_KEYS,
    HybridScoreFollower,
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
