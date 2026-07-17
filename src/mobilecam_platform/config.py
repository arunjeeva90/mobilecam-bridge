from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(slots=True)
class SourceConfig:
    kind: str = "rtsp"
    uri: str = "rtsp://192.168.1.100:8554/live"
    backend: str = "auto"
    width: int = 1280
    height: int = 720
    fps: int = 30
    reconnect_delay_s: float = 1.0
    buffer_size: int = 1


@dataclass(slots=True)
class AndroidControlConfig:
    enabled: bool = False
    base_url: str = "http://192.168.1.100:8080"
    camera_endpoint: str = "/api/v1/camera"
    method: str = "POST"
    timeout_s: float = 3.0
    front_value: str = "front"
    rear_value: str = "rear"


@dataclass(slots=True)
class OutputConfig:
    record_directory: str = "outputs/recordings"
    snapshot_directory: str = "outputs/snapshots"


@dataclass(slots=True)
class AppConfig:
    name: str = "Android Phone Camera"
    source: SourceConfig = field(default_factory=SourceConfig)
    android_control: AndroidControlConfig = field(default_factory=AndroidControlConfig)
    output: OutputConfig = field(default_factory=OutputConfig)


def _section(cls: type, data: dict[str, Any] | None):
    valid = cls.__dataclass_fields__.keys()
    return cls(**{k: v for k, v in (data or {}).items() if k in valid})


def load_config(path: str | Path) -> AppConfig:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    return AppConfig(
        name=str(raw.get("name", "Android Phone Camera")),
        source=_section(SourceConfig, raw.get("source")),
        android_control=_section(AndroidControlConfig, raw.get("android_control")),
        output=_section(OutputConfig, raw.get("output")),
    )
