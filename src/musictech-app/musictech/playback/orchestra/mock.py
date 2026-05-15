"""Console-only playback stub for dispatcher integration tests.

Subscribes to a :class:`ScoreEventDispatcher` and logs every index
change and tempo step. Used by ``playback_validator.py`` and unit
tests to verify the dispatcher fan-out without depending on
``pygame.midi`` or audio hardware.
"""

from __future__ import annotations

import logging

from ..event_dispatcher import ScoreEventDispatcher
from ..tempo_tracker import TempoTracker

__all__ = ["MockOrchestraPlayer"]


class MockOrchestraPlayer:
    """Console-only playback stub for dispatcher integration tests."""

    def __init__(
        self,
        dispatcher: ScoreEventDispatcher,
        *,
        tempo_change_threshold: float = 0.05,
        logger: logging.Logger | None = None,
    ) -> None:
        if tempo_change_threshold < 0.0:
            raise ValueError("tempo_change_threshold must be non-negative")

        self.dispatcher = dispatcher
        self.tempo_change_threshold = float(tempo_change_threshold)
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self._last_logged_index: int | None = None
        self._last_logged_tempo: float | None = None

        self.dispatcher.subscribe(self.handle_dispatch)

    def close(self) -> None:
        self.dispatcher.unsubscribe(self.handle_dispatch)

    def handle_dispatch(self, index: int, tempo_ratio: float) -> None:
        if self._last_logged_index != index:
            self.logger.info("Orchestra jumping to measure/index %d", index)
            self._last_logged_index = int(index)

        if self._should_log_tempo(tempo_ratio):
            self.logger.info("Orchestra adjusting playback speed to %.2fx", tempo_ratio)
            self._last_logged_tempo = float(tempo_ratio)

    def _should_log_tempo(self, tempo_ratio: float) -> bool:
        if self._last_logged_tempo is None:
            return True

        baseline = max(abs(self._last_logged_tempo), TempoTracker._MIN_ELAPSED)
        relative_change = abs(tempo_ratio - self._last_logged_tempo) / baseline
        return relative_change > self.tempo_change_threshold
