from __future__ import annotations

import platform
from typing import Any

import cv2
import numpy as np

from ..config import SourceConfig
from .base import VideoBackend


class OpenCVBackend(VideoBackend):
    def __init__(self, config: SourceConfig):
        self.config = config
        self.capture: cv2.VideoCapture | None = None

    def _source(self) -> Any:
        if self.config.kind.lower() in {"uvc", "device"}:
            try:
                return int(self.config.uri)
            except ValueError:
                return self.config.uri
        return self.config.uri

    def _api(self) -> int:
        requested = self.config.backend.lower()
        if requested == "ffmpeg":
            return cv2.CAP_FFMPEG
        if requested == "gstreamer":
            return cv2.CAP_GSTREAMER
        if requested == "v4l2":
            return cv2.CAP_V4L2
        if requested == "dshow":
            return cv2.CAP_DSHOW
        if self.config.kind.lower() in {"uvc", "device"}:
            return cv2.CAP_DSHOW if platform.system() == "Windows" else cv2.CAP_V4L2
        return cv2.CAP_FFMPEG

    def open(self) -> None:
        self.close()
        self.capture = cv2.VideoCapture(self._source(), self._api())
        self.capture.set(cv2.CAP_PROP_BUFFERSIZE, self.config.buffer_size)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.width)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.height)
        self.capture.set(cv2.CAP_PROP_FPS, self.config.fps)
        if not self.capture.isOpened():
            self.close()
            raise RuntimeError(f"Unable to open video source: {self.config.uri}")

    def read(self) -> np.ndarray | None:
        if self.capture is None:
            return None
        ok, frame = self.capture.read()
        return frame if ok else None

    def close(self) -> None:
        if self.capture is not None:
            self.capture.release()
        self.capture = None

    @property
    def is_open(self) -> bool:
        return bool(self.capture is not None and self.capture.isOpened())
