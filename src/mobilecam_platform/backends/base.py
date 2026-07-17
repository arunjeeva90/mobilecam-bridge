from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np


class VideoBackend(ABC):
    @abstractmethod
    def open(self) -> None: ...

    @abstractmethod
    def read(self) -> np.ndarray | None: ...

    @abstractmethod
    def close(self) -> None: ...

    @property
    @abstractmethod
    def is_open(self) -> bool: ...
