"""Worker-thread fan-out from follower predictions to subscribers.

The dispatcher decouples the follower's hot path (which must stay
under ~5 ms per event) from heavier downstream consumers like the
orchestra renderer. Events are pushed onto a bounded queue and
delivered to subscribers on a daemon worker thread.

Drop policy: if the queue is full, the oldest event is dropped and a
warning is logged. This matches the realtime contract — we prefer a
recent prediction over a stale one.
"""

from __future__ import annotations

import logging
import queue
import threading
import time
from pathlib import Path
from typing import Any

from .events import DispatchCallback, DispatchEvent
from .tempo_tracker import TempoTracker

__all__ = ["ScoreEventDispatcher"]


class ScoreEventDispatcher:
    """Fan out follower predictions to playback subscribers on a worker thread."""

    _SENTINEL = object()

    def __init__(
        self,
        score_json: str | Path | dict[str, Any] | list[dict[str, Any]],
        *,
        tempo_tracker: TempoTracker | None = None,
        queue_maxsize: int = 0,
        autostart: bool = True,
    ) -> None:
        self.tempo_tracker = tempo_tracker or TempoTracker(score_json)
        self._queue: queue.Queue[DispatchEvent | object] = queue.Queue(maxsize=queue_maxsize)
        self._callbacks: list[DispatchCallback] = []
        self._callbacks_lock = threading.RLock()
        self._worker_lock = threading.Lock()
        self._stop_event = threading.Event()
        self._worker: threading.Thread | None = None

        self.current_index: int | None = None
        self.current_tempo_ratio = float(self.tempo_tracker.tempo_ratio)
        self.current_event_timestamp: float | None = None
        self.last_broadcast_wall_time: float | None = None

        if autostart:
            self.start()

    def start(self) -> None:
        """Spin up the worker thread if it is not already running."""
        with self._worker_lock:
            if self._worker is not None and self._worker.is_alive():
                return

            self._stop_event.clear()
            self._worker = threading.Thread(
                target=self._worker_loop,
                name="ScoreEventDispatcher",
                daemon=True,
            )
            self._worker.start()

    def subscribe(self, callback: DispatchCallback) -> None:
        """Register ``callback(score_index, tempo_ratio)`` for every event."""
        with self._callbacks_lock:
            if callback not in self._callbacks:
                self._callbacks.append(callback)

    def unsubscribe(self, callback: DispatchCallback) -> None:
        with self._callbacks_lock:
            if callback in self._callbacks:
                self._callbacks.remove(callback)

    def broadcast(
        self,
        current_index: int,
        timestamp: float,
        *,
        tempo_update: bool = True,
    ) -> None:
        """Enqueue one follower prediction for downstream delivery."""
        self.start()
        event = DispatchEvent(
            index=int(current_index),
            timestamp=float(timestamp),
            tempo_update=bool(tempo_update),
        )
        self.last_broadcast_wall_time = time.monotonic()

        try:
            self._queue.put_nowait(event)
            return
        except queue.Full:
            pass

        try:
            dropped = self._queue.get_nowait()
            self._queue.task_done()
            if dropped is not self._SENTINEL:
                logging.warning("ScoreEventDispatcher queue overflow, dropping stale event")
        except queue.Empty:
            pass

        self._queue.put_nowait(event)

    def flush(self, timeout: float = 2.0) -> bool:
        """Block until all enqueued events are delivered or ``timeout`` elapses."""
        deadline = time.monotonic() + max(0.0, timeout)
        while time.monotonic() < deadline:
            if self._queue.unfinished_tasks == 0:
                return True
            time.sleep(0.01)
        return self._queue.unfinished_tasks == 0

    def clear_pending(self) -> int:
        """Discard everything still queued. Returns the number of dropped events."""
        cleared = 0
        while True:
            try:
                item = self._queue.get_nowait()
            except queue.Empty:
                break

            self._queue.task_done()
            if item is self._SENTINEL:
                self._queue.put_nowait(item)
                break

            cleared += 1
        return cleared

    def close(self, timeout: float = 1.0) -> None:
        """Stop the worker thread and release its resources."""
        thread: threading.Thread | None
        with self._worker_lock:
            thread = self._worker
            self._stop_event.set()

        if thread is None:
            return

        while True:
            try:
                self._queue.put(self._SENTINEL, timeout=0.05)
                break
            except queue.Full:
                if not thread.is_alive():
                    break

        if thread.is_alive():
            thread.join(timeout=timeout)

        with self._worker_lock:
            if self._worker is thread and not thread.is_alive():
                self._worker = None

    def __enter__(self) -> "ScoreEventDispatcher":
        self.start()
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.close()

    def _worker_loop(self) -> None:
        while True:
            try:
                item = self._queue.get(timeout=0.05)
            except queue.Empty:
                if self.tempo_tracker.maybe_reset_idle(time.monotonic()):
                    self.current_tempo_ratio = float(self.tempo_tracker.tempo_ratio)
                if self._stop_event.is_set():
                    return
                continue

            try:
                if item is self._SENTINEL:
                    return

                assert isinstance(item, DispatchEvent)
                if item.tempo_update:
                    tempo_ratio = float(self.tempo_tracker.update(item.index, item.timestamp))
                else:
                    tempo_ratio = float(self.current_tempo_ratio)
                self.current_index = item.index
                self.current_tempo_ratio = tempo_ratio
                self.current_event_timestamp = item.timestamp

                with self._callbacks_lock:
                    callbacks = tuple(self._callbacks)

                for callback in callbacks:
                    try:
                        callback(item.index, tempo_ratio)
                    except Exception:
                        logging.exception("ScoreEventDispatcher callback failed")
            finally:
                self._queue.task_done()
