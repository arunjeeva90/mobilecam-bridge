from __future__ import annotations

import queue
import threading
import time
from dataclasses import dataclass

import numpy as np

from .backends import OpenCVBackend
from .config import AppConfig


@dataclass(slots=True)
class FramePacket:
    frame: np.ndarray
    timestamp_ns: int
    sequence: int
    source_name: str


class FrameProvider:
    """Threaded latest-frame provider with bounded buffering and reconnect."""

    def __init__(self, config: AppConfig):
        self.config = config
        self.backend = OpenCVBackend(config.source)
        self._queue: queue.Queue[FramePacket] = queue.Queue(maxsize=1)
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._sequence = 0
        self.last_error: str | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="mobilecam-capture", daemon=True)
        self._thread.start()

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                if not self.backend.is_open:
                    self.backend.open()
                frame = self.backend.read()
                if frame is None:
                    raise RuntimeError("Video source returned no frame")
                self.last_error = None
                packet = FramePacket(
                    frame=frame,
                    timestamp_ns=time.monotonic_ns(),
                    sequence=self._sequence,
                    source_name=self.config.name,
                )
                self._sequence += 1
                while not self._queue.empty():
                    try:
                        self._queue.get_nowait()
                    except queue.Empty:
                        break
                self._queue.put_nowait(packet)
            except Exception as exc:
                self.last_error = str(exc)
                self.backend.close()
                self._stop.wait(self.config.source.reconnect_delay_s)

    def read(self, timeout_s: float = 1.0) -> FramePacket | None:
        try:
            return self._queue.get(timeout=timeout_s)
        except queue.Empty:
            return None

    def stop(self) -> None:
        self._stop.set()
        self.backend.close()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._thread = None
