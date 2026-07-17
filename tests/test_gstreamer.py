from mobilecam_platform.adapters import build_gstreamer_pipeline
from mobilecam_platform.config import SourceConfig


def test_axon_pipeline_uses_mpp_decoder():
    pipeline = build_gstreamer_pipeline(SourceConfig(kind="rtsp", uri="rtsp://x/live"), "axon")
    assert "mppvideodec" in pipeline
    assert "appsink" in pipeline


def test_uvc_pipeline_uses_v4l2():
    pipeline = build_gstreamer_pipeline(SourceConfig(kind="uvc", uri="/dev/video2"))
    assert "v4l2src device=/dev/video2" in pipeline
