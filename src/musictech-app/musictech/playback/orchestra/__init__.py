"""Orchestra renderers that consume :class:`ScoreEventDispatcher` updates.

We ship two simple renderers here (mock console logger and one-chord-
per-event ``pygame.midi`` player). The "real" sample-based renderer
(:class:`DynamicOrchestraPlayer`) still lives at
``midi/real_orchestra_player.py`` — it is large, self-contained, and
not refactored into this package.
"""

from .mock import MockOrchestraPlayer
from .pygame_midi import PygameMidiOrchestra

__all__ = [
    "MockOrchestraPlayer",
    "PygameMidiOrchestra",
]
