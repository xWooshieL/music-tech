"""Tempo tracking from score progress and event timestamps.

The tracker estimates ``tempo_ratio = nominal_elapsed / actual_elapsed``
over the last few score-state changes. The ratio feeds the orchestra
renderer so it can stretch / compress the accompaniment in realtime.

The actual estimator is intentionally simple:

- Keep up to ``history_size`` recent ``(position, event_time)`` control
  points.
- For each new position change, compute one observation per anchor in
  the history that is at least ``min_nominal_window`` seconds away on
  the score timeline.
- The new ``tempo_ratio`` is the **median** of the raw observations,
  with a dead-zone (``deadzone_ratio``) to avoid flickering and an
  ``idle_reset_seconds`` timeout that snaps back to the initial ratio
  when the performer stops playing.

Anything more sophisticated (Kalman / RL agent) belongs to the
``musictech.rl`` layer and consumes this tracker as a baseline.
"""

from __future__ import annotations

import logging
from collections import deque
from pathlib import Path
from typing import Any, Deque

import numpy as np

from .events import TempoObservation
from .score_loader import load_score

__all__ = ["TempoTracker"]


class TempoTracker:
    """Estimate performance tempo from score progress and event timestamps."""

    _MIN_ELAPSED = 1e-6

    def __init__(
        self,
        score_json: str | Path | dict[str, Any] | list[dict[str, Any]],
        *,
        history_size: int = 5,
        smoothing_factor: float = 1.0,
        initial_tempo_ratio: float = 1.0,
        min_tempo_ratio: float = 0.25,
        max_tempo_ratio: float = 4.0,
        deadzone_ratio: float = 0.02,
        min_nominal_window: float = 0.18,
        variance_warn_threshold: float = 0.0,
        variance_log_interval: int = 1,
        idle_reset_seconds: float = 1.5,
    ) -> None:
        if history_size < 1:
            raise ValueError("history_size must be at least 1")
        if initial_tempo_ratio <= 0.0:
            raise ValueError("initial_tempo_ratio must be positive")
        if min_tempo_ratio <= 0.0 or max_tempo_ratio <= 0.0:
            raise ValueError("tempo ratio bounds must be positive")
        if min_tempo_ratio > max_tempo_ratio:
            raise ValueError("min_tempo_ratio must be <= max_tempo_ratio")
        if min_nominal_window <= 0.0:
            raise ValueError("min_nominal_window must be positive")
        if idle_reset_seconds <= 0.0:
            raise ValueError("idle_reset_seconds must be positive")

        _, notes = load_score(score_json)
        self.state_indices = np.asarray(
            [int(note.get("index", position)) for position, note in enumerate(notes)],
            dtype=np.int64,
        )
        self.index_to_position = {
            int(score_index): position for position, score_index in enumerate(self.state_indices)
        }
        self.nominal_durations = np.maximum(
            np.asarray([float(note["nominal_duration"]) for note in notes], dtype=np.float64),
            self._MIN_ELAPSED,
        )
        self.cumulative_nominal_time = np.concatenate(
            (
                np.zeros(1, dtype=np.float64),
                np.cumsum(self.nominal_durations, dtype=np.float64),
            )
        )
        self.nominal_onsets = np.asarray(
            [
                float(note.get("nominal_onset", self.cumulative_nominal_time[position]))
                for position, note in enumerate(notes)
            ],
            dtype=np.float64,
        )

        self.history_size = int(history_size)
        self.smoothing_factor = float(smoothing_factor)
        self.min_tempo_ratio = float(min_tempo_ratio)
        self.max_tempo_ratio = float(max_tempo_ratio)
        self.deadzone_ratio = float(deadzone_ratio)
        self.min_nominal_window = float(min_nominal_window)
        self.variance_warn_threshold = float(variance_warn_threshold)
        self.variance_log_interval = int(variance_log_interval)
        self.idle_reset_seconds = float(idle_reset_seconds)
        self._initial_tempo_ratio = float(initial_tempo_ratio)
        self.tempo_ratio = float(initial_tempo_ratio)
        self.recent_observations: Deque[TempoObservation] = deque(maxlen=self.history_size)
        self.recent_tempo_ratios: Deque[float] = deque(
            [self.tempo_ratio],
            maxlen=self.history_size,
        )
        self.recent_control_points: Deque[tuple[int, float]] = deque(
            maxlen=self.history_size + 1,
        )
        self.last_variance = 0.0
        self._update_count = 0
        self._logger = logging.getLogger(self.__class__.__name__)

        self.last_index: int | None = None
        self.last_position: int | None = None
        self.last_change_timestamp: float | None = None

    def update(self, score_index: int, timestamp: float) -> float:
        """Update the tempo ratio from one new ``(score_index, timestamp)`` pair."""
        position = self._position_for_index(score_index)
        event_time = float(timestamp)

        if self.last_change_timestamp is not None and event_time < self.last_change_timestamp:
            event_time = self.last_change_timestamp

        if self.last_position is None or self.last_change_timestamp is None:
            self.last_index = int(score_index)
            self.last_position = position
            self.last_change_timestamp = event_time
            self.recent_control_points.clear()
            self.recent_control_points.append((position, event_time))
            return self.tempo_ratio

        idle_gap = event_time - self.last_change_timestamp
        if idle_gap > self.idle_reset_seconds:
            self.reset()
            self.last_index = int(score_index)
            self.last_position = position
            self.last_change_timestamp = event_time
            self.recent_control_points.append((position, event_time))
            return self.tempo_ratio

        if position == self.last_position:
            return self.tempo_ratio

        self.recent_control_points.append((position, event_time))
        raw_observations: list[TempoObservation] = []

        for anchor_position, anchor_time in self.recent_control_points:
            if anchor_position == position:
                continue

            nominal_elapsed = abs(
                float(self.nominal_onsets[position] - self.nominal_onsets[anchor_position])
            )
            if nominal_elapsed <= self._MIN_ELAPSED:
                nominal_elapsed = abs(
                    float(
                        self.cumulative_nominal_time[position]
                        - self.cumulative_nominal_time[anchor_position]
                    )
                )
            if nominal_elapsed < self.min_nominal_window:
                continue

            actual_elapsed = max(self._MIN_ELAPSED, abs(event_time - anchor_time))
            raw_ratio = float(
                np.clip(
                    nominal_elapsed / actual_elapsed,
                    self.min_tempo_ratio,
                    self.max_tempo_ratio,
                )
            )
            raw_observations.append(
                TempoObservation(
                    nominal_elapsed=nominal_elapsed,
                    actual_elapsed=actual_elapsed,
                    raw_ratio=raw_ratio,
                )
            )

        if raw_observations:
            representative_observation = max(
                raw_observations,
                key=lambda observation: observation.nominal_elapsed,
            )
            self.recent_observations.append(representative_observation)
            previous_ratio = float(self.tempo_ratio)
            history = np.asarray(
                [sample.raw_ratio for sample in self.recent_observations],
                dtype=np.float64,
            )
            smoothed_ratio = float(np.median(history))
            if self.smoothing_factor < 1.0:
                smoothed_ratio = float(
                    previous_ratio
                    + (np.clip(self.smoothing_factor, 0.0, 1.0) * (smoothed_ratio - previous_ratio))
                )
            baseline = max(abs(previous_ratio), self._MIN_ELAPSED)
            relative_change = abs(smoothed_ratio - previous_ratio) / baseline
            if relative_change >= self.deadzone_ratio:
                self.tempo_ratio = smoothed_ratio
            self.last_variance = float(np.var(history, dtype=np.float64))
            self.recent_tempo_ratios.append(float(self.tempo_ratio))
        elif self.recent_observations:
            history = np.asarray(
                [sample.raw_ratio for sample in self.recent_observations],
                dtype=np.float64,
            )
            self.last_variance = float(np.var(history, dtype=np.float64))
        else:
            self.last_variance = 0.0

        self._update_count += 1

        self.last_index = int(score_index)
        self.last_position = position
        self.last_change_timestamp = event_time
        return self.tempo_ratio

    def reset(self) -> None:
        """Reset the tempo ratio and clear all history."""
        self.tempo_ratio = self._initial_tempo_ratio
        self.recent_observations.clear()
        self.recent_tempo_ratios.clear()
        self.recent_tempo_ratios.append(self.tempo_ratio)
        self.recent_control_points.clear()
        self.last_index = None
        self.last_position = None
        self.last_change_timestamp = None
        self.last_variance = 0.0
        self._update_count = 0

    def maybe_reset_idle(self, current_time: float) -> bool:
        """Reset state if no new event arrived within ``idle_reset_seconds``."""
        if self.last_change_timestamp is None:
            return False
        if (float(current_time) - self.last_change_timestamp) <= self.idle_reset_seconds:
            return False
        if abs(self.tempo_ratio - self._initial_tempo_ratio) <= 1e-6:
            return False
        self.reset()
        return True

    def _position_for_index(self, score_index: int) -> int:
        try:
            return int(self.index_to_position[int(score_index)])
        except KeyError as exc:
            raise ValueError(f"Unknown score index: {score_index}") from exc

    def _log_variance_if_needed(self, raw_std: float, effective_smoothing: float) -> None:
        del raw_std, effective_smoothing
        return
