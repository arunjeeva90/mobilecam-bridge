from __future__ import annotations

import requests

from .config import AndroidControlConfig


class AndroidCameraController:
    def __init__(self, config: AndroidControlConfig):
        self.config = config

    def switch(self, lens: str) -> None:
        if lens not in {"front", "rear"}:
            raise ValueError("lens must be 'front' or 'rear'")
        if not self.config.enabled:
            raise RuntimeError("Android camera control is disabled in the active profile")

        value = self.config.front_value if lens == "front" else self.config.rear_value
        url = self.config.base_url.rstrip("/") + "/" + self.config.camera_endpoint.lstrip("/")
        payload = {"lens": value}
        method = self.config.method.upper()
        if method == "POST":
            response = requests.post(url, json=payload, timeout=self.config.timeout_s)
        elif method == "PUT":
            response = requests.put(url, json=payload, timeout=self.config.timeout_s)
        else:
            response = requests.get(url, params=payload, timeout=self.config.timeout_s)
        response.raise_for_status()
