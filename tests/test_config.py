from pathlib import Path

from mobilecam_platform.config import load_config


def test_load_config(tmp_path: Path):
    path = tmp_path / "profile.yaml"
    path.write_text("name: Test\nsource:\n  kind: rtsp\n  uri: rtsp://host/live\n", encoding="utf-8")
    config = load_config(path)
    assert config.name == "Test"
    assert config.source.uri == "rtsp://host/live"
