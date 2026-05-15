"""File-based MIDI source that replays a ``.mid`` file in realtime."""

from __future__ import annotations

import queue
import threading
from pathlib import Path
from typing import Any

from ._helpers import MidiEvent, _drain_queue, _push_event, _require_mido

__all__ = ["MidiEmulator"]


class MidiEmulator:
    """Replay note events from a MIDI file on a background thread."""

    def __init__(
        self,
        midi_file_path: str | Path,
        *,
        event_queue: "queue.Queue[MidiEvent] | None" = None,
        max_queue_size: int = 0,
        loop: bool = False,
        start_immediately: bool = False,
    ) -> None:
        self._midi_file_path = Path(midi_file_path)
        self._events = (
            event_queue if event_queue is not None else queue.Queue(maxsize=max_queue_size)
        )
        self._loop = loop
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

        if start_immediately:
            self.start()

    def start(self) -> None:
        """Start replaying the MIDI file in real time."""
        midi_lib = _require_mido()

        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return

            midi_lib.MidiFile(self._midi_file_path)
            self._stop_event.clear()
            self._thread = threading.Thread(
                target=self._play_loop,
                name="MidiEmulator",
                daemon=True,
            )
            self._thread.start()

    def close(self, timeout: float = 1.0) -> None:
        """Stop playback without blocking longer than timeout."""
        thread: threading.Thread | None = None

        with self._lock:
            self._stop_event.set()
            thread = self._thread

        if thread is not None and thread.is_alive():
            thread.join(timeout=timeout)

        with self._lock:
            if self._thread is thread and (thread is None or not thread.is_alive()):
                self._thread = None

    def get_events(self) -> list[MidiEvent]:
        """Return all currently buffered events without blocking."""
        return _drain_queue(self._events)

    @property
    def event_queue(self) -> "queue.Queue[MidiEvent]":
        return self._events

    @property
    def is_running(self) -> bool:
        thread = self._thread
        return thread is not None and thread.is_alive()

    def __enter__(self) -> "MidiEmulator":
        self.start()
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.close()

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass

    def _play_loop(self) -> None:
        midi_lib = _require_mido()

        try:
            while not self._stop_event.is_set():
                midi_file = midi_lib.MidiFile(self._midi_file_path)

                for msg in midi_file:
                    delay = max(0.0, float(getattr(msg, "time", 0.0)))
                    if delay and self._stop_event.wait(delay):
                        return

                    if (
                        getattr(msg, "type", None) == "note_on"
                        and getattr(msg, "velocity", 0) > 0
                    ):
                        _push_event(self._events, getattr(msg, "note"))

                if not self._loop:
                    break
        finally:
            self._stop_event.set()
            with self._lock:
                if self._thread is threading.current_thread():
                    self._thread = None
