"""Score followers (HMM, HSMM, OLTW, Hybrid).

Each follower is a pure-numpy state-machine that consumes one MIDI
``note_on`` per call and produces a score index. They share the same
``process_event(pitch, timestamp) -> int`` shape so the rest of the
pipeline (output dispatcher, RL environment) does not need to know
which model is active.

The hybrid follower lives in its own sub-package because it carries
helper logic (anchor recovery, profile loading) that justifies multiple
files.
"""

from .hmm import ScoreFollowerHMM
from .hsmm import ScoreFollowerHSMM
from .oltw import ScoreFollowerOLTW
from .hybrid import HybridScoreFollower

__all__ = [
    "HybridScoreFollower",
    "ScoreFollowerHMM",
    "ScoreFollowerHSMM",
    "ScoreFollowerOLTW",
]
