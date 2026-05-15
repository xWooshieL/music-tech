"""Simple ``pygame.midi`` orchestra: one chord per dispatcher event.

Used as the default accompaniment renderer in the legacy CLI
pipeline. Each follower-confirmed index triggers a brief chord at
fixed velocity; the chord's release time is scaled by the current
tempo ratio so the accompaniment stays in sync with the performer.

For the richer sample-based orchestra (Philharmonia Strings, CC
expression, reverb), see ``midi/real_orchestra_player.py`` —
that 1.3 KLOC class is intentionally untouched by this refactor.
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Any

import numpy as np

try:
    import pygame
    import pygame.midi
except ModuleNotFoundError:
    pygame = None

from ..event_dispatcher import ScoreEventDispatcher
from ..score_loader import load_score, note_pitches

__all__ = ["PygameMidiOrchestra"]


class PygameMidiOrchestra:
    """Play short MIDI piano accompaniment chords from dispatcher updates."""

    def __init__(
        self,
        dispatcher: ScoreEventDispatcher,
        score_json: str | Path | dict[str, Any] | list[dict[str, Any]],
        *,
        instrument_program: int = 0,
        midi_channel: int = 0,
        velocity: int = 76,
        base_chord_duration: float = 0.42,
        logger: logging.Logger | None = None,
    ) -> None:
        if not 0 <= instrument_program <= 127:
            raise ValueError("instrument_program must be in the range [0, 127]")
        if not 0 <= midi_channel <= 15:
            raise ValueError("midi_channel must be in the range [0, 15]")
        if not 0 <= velocity <= 127:
            raise ValueError("velocity must be in the range [0, 127]")
        if base_chord_duration <= 0.0:
            raise ValueError("base_chord_duration must be positive")

        _, notes = load_score(score_json)
        self.state_indices = np.asarray(
            [int(note.get("index", position)) for position, note in enumerate(notes)],
            dtype=np.int64,
        )
        self.index_to_position = {
            int(score_index): position for position, score_index in enumerate(self.state_indices)
        }
        self.score_chords = [
            sorted({int(np.clip(pitch, 0, 127)) for pitch in note_pitches(note)})
            for note in notes
        ]
        self.score_pitches = np.asarray(
            [max(chord) for chord in self.score_chords],
            dtype=np.int64,
        )

        self.dispatcher = dispatcher
        self.instrument_program = int(instrument_program)
        self.midi_channel = int(midi_channel)
        self.velocity = int(velocity)
        self.base_chord_duration = float(base_chord_duration)
        self.logger = logger or logging.getLogger(self.__class__.__name__)

        self._lock = threading.RLock()
        self._output: Any = None
        self._initialized_midi = False
        self._active_notes: list[int] = []
        self._last_index: int | None = None
        self._release_timer: threading.Timer | None = None
        self._playback_token = 0
        self.is_available = False
        self.status_label = "MIDI orchestra unavailable"

        self.dispatcher.subscribe(self.handle_dispatch)
        self._open_output()

    def close(self) -> None:
        self.dispatcher.unsubscribe(self.handle_dispatch)
        with self._lock:
            self._cancel_release_timer_locked()
            self._stop_active_notes_locked()
            output = self._output
            self._output = None
            initialized_midi = self._initialized_midi
            self._initialized_midi = False

        if output is not None:
            try:
                output.close()
            except Exception:
                self.logger.exception("Failed to close MIDI output cleanly")

        if initialized_midi and pygame is not None and pygame.midi.get_init():
            try:
                pygame.midi.quit()
            except Exception:
                self.logger.exception("Failed to quit pygame.midi cleanly")

        self.is_available = False

    def panic(self) -> None:
        """Force-release every active MIDI note (for stop / pause)."""
        with self._lock:
            self._cancel_release_timer_locked()
            self._stop_active_notes_locked()
            self._last_index = None

    def handle_dispatch(self, index: int, tempo_ratio: float) -> None:
        if not self.is_available:
            return

        with self._lock:
            if self._output is None or index == self._last_index:
                return

            self._last_index = int(index)
            self._cancel_release_timer_locked()
            self._stop_active_notes_locked()

            chord_notes = self._chord_for_index(index)
            for note in chord_notes:
                self._output.note_on(int(note), self.velocity, self.midi_channel)
            self._active_notes = chord_notes

            release_after = float(
                np.clip(
                    self.base_chord_duration / max(tempo_ratio, 0.35),
                    0.14,
                    0.75,
                )
            )
            self._playback_token += 1
            token = self._playback_token
            timer = threading.Timer(release_after, self._release_if_current, args=(token,))
            timer.daemon = True
            self._release_timer = timer
            timer.start()

    def _open_output(self) -> None:
        if pygame is None:
            self.logger.warning("pygame.midi is not installed; disabling MIDI orchestra")
            self.status_label = "MIDI orchestra unavailable"
            return

        try:
            if not pygame.midi.get_init():
                pygame.midi.init()
                self._initialized_midi = True

            output_id = pygame.midi.get_default_output_id()
            if output_id < 0:
                output_id = self._first_output_device_id()
            if output_id < 0:
                self.logger.warning("No MIDI output device found; disabling MIDI orchestra")
                self.status_label = "MIDI orchestra unavailable"
                return

            self._output = pygame.midi.Output(output_id, latency=0)
            self._output.set_instrument(self.instrument_program, self.midi_channel)
            self.is_available = True
            self.status_label = f"Piano via MIDI (Program {self.instrument_program})"
        except Exception:
            self.logger.exception("Failed to initialize MIDI orchestra")
            self.status_label = "MIDI orchestra unavailable"
            self.is_available = False
            if self._output is not None:
                try:
                    self._output.close()
                except Exception:
                    pass
                self._output = None

    def _first_output_device_id(self) -> int:
        assert pygame is not None
        for device_id in range(pygame.midi.get_count()):
            device_info = pygame.midi.get_device_info(device_id)
            if device_info is None:
                continue
            is_output = bool(device_info[3])
            if is_output:
                return int(device_id)
        return -1

    def _position_for_index(self, score_index: int) -> int:
        try:
            return int(self.index_to_position[int(score_index)])
        except KeyError:
            return int(np.clip(score_index, 0, len(self.score_pitches) - 1))

    def _chord_for_index(self, score_index: int) -> list[int]:
        position = self._position_for_index(score_index)
        return list(self.score_chords[position])

    def _release_if_current(self, token: int) -> None:
        with self._lock:
            if token != self._playback_token:
                return
            self._release_timer = None
            self._stop_active_notes_locked()

    def _cancel_release_timer_locked(self) -> None:
        if self._release_timer is None:
            return
        self._release_timer.cancel()
        self._release_timer = None

    def _stop_active_notes_locked(self) -> None:
        if self._output is None or not self._active_notes:
            self._active_notes = []
            return

        for note in self._active_notes:
            try:
                self._output.note_off(int(note), 0, self.midi_channel)
            except Exception:
                self.logger.exception("Failed to stop MIDI note %s", note)
        self._active_notes = []
