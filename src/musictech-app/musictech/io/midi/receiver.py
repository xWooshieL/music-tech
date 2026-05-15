"""Hardware MIDI input receiver running on a background thread."""

from __future__ import annotations

import queue
import threading
from typing import Any

from ._helpers import MidiEvent, _drain_queue, _push_event, _require_mido

__all__ = ["LiveMidiReceiver"]


class LiveMidiReceiver:
    """Receive live MIDI note events on a background thread."""

    def __init__(
        self,
        port_name: str | None = None,
        *,
        poll_interval: float = 0.01,
        max_queue_size: int = 0,
        event_queue: "queue.Queue[MidiEvent] | None" = None,
        open_immediately: bool = True,
    ) -> None:
        if poll_interval <= 0:
            raise ValueError("poll_interval must be positive")

        self._port_name = port_name
        self._poll_interval = poll_interval
        self._events = (
            event_queue if event_queue is not None else queue.Queue(maxsize=max_queue_size)
        )
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._port: Any | None = None
        self._lock = threading.Lock()

        if open_immediately:
            self.start()

    def start(self) -> None:
        """Open the MIDI input port and start the listener thread."""
        midi_lib = _require_mido()

        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return

            self._stop_event.clear()
            self._port = midi_lib.open_input(self._port_name)
            self._thread = threading.Thread(
                target=self._listen_loop,
                name="LiveMidiReceiver",
                daemon=True,
            )
            self._thread.start()

    def close(self, timeout: float = 1.0) -> None:
        """Stop the listener and close the MIDI port."""
        thread: threading.Thread | None = None
        port: Any | None = None

        with self._lock:
            self._stop_event.set()
            thread = self._thread
            port = self._port

        if port is not None:
            try:
                port.close()
            except Exception:
                pass

        if thread is not None and thread.is_alive():
            thread.join(timeout=timeout)

        with self._lock:
            if self._port is port:
                self._port = None
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

    def __enter__(self) -> "LiveMidiReceiver":
        self.start()
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.close()

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass

    def _listen_loop(self) -> None:
        port = self._port
        if port is None:
            return

        try:
            while not self._stop_event.is_set():
                try:
                    messages = list(port.iter_pending())
                except Exception:
                    break

                for msg in messages:
                    if (
                        getattr(msg, "type", None) == "note_on"
                        and getattr(msg, "velocity", 0) > 0
                    ):
                        _push_event(self._events, getattr(msg, "note"))

                self._stop_event.wait(self._poll_interval)
        finally:
            try:
                port.close()
            except Exception:
                pass
            finally:
                with self._lock:
                    if self._port is port:
                        self._port = None
                    if self._thread is threading.current_thread():
                        self._thread = None
