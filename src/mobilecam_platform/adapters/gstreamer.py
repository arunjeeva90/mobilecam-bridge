from __future__ import annotations

from ..config import SourceConfig


def build_gstreamer_pipeline(source: SourceConfig, target: str = "generic") -> str:
    uri = source.uri
    target = target.lower()
    if source.kind == "rtsp":
        decoder = "decodebin"
        if target in {"axon", "rk3588"}:
            decoder = "rtph264depay ! h264parse ! mppvideodec"
        elif target in {"ti", "tidl", "tda4"}:
            decoder = "rtph264depay ! h264parse ! v4l2h264dec"
        return (
            f'rtspsrc location="{uri}" latency=100 drop-on-latency=true ! '
            f"{decoder} ! videoconvert ! video/x-raw,format=BGR ! appsink drop=true max-buffers=1"
        )
    if source.kind in {"uvc", "device"}:
        return (
            f"v4l2src device={uri} ! video/x-raw,width={source.width},height={source.height},"
            f"framerate={source.fps}/1 ! videoconvert ! video/x-raw,format=BGR ! "
            "appsink drop=true max-buffers=1"
        )
    return f'uridecodebin uri="{uri}" ! videoconvert ! video/x-raw,format=BGR ! appsink'
