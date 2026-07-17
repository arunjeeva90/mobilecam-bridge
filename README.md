# MobileCam Bridge

[![CI](https://github.com/arunjeeva90/mobilecam-bridge/actions/workflows/ci.yml/badge.svg)](https://github.com/arunjeeva90/mobilecam-bridge/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Apache--2.0-green.svg)](LICENSE)

**MobileCam Bridge** turns an Android phone into a reusable primary camera input for computer-vision and edge-AI applications. It provides one common acquisition layer for Windows, Linux, Vicharak AXON/RK3588, TI Jacinto/TIDL, OpenCV and GStreamer environments.

The platform is intentionally separated from ADAS, DMS and inference logic. Integration-specific branches can consume the same timestamped frame interface without rebuilding camera acquisition for every target.

## Key capabilities

- Select the Android **front or rear camera** from the desktop GUI when the phone streaming application exposes the control API.
- Receive **RTSP**, **HTTP/MJPEG** and local **USB/UVC** video.
- Use Windows DirectShow or Linux V4L2/OpenCV capture paths.
- Preview live video with FPS, frame age and reconnect status.
- Save snapshots and MP4 recordings.
- Run through the PySide6 GUI or a headless CLI.
- Feed normalized BGR frames and monotonic timestamps into downstream processing.
- Generate GStreamer pipelines suitable for Linux, AXON and TI environments.
- Store reusable device profiles in YAML.

## Architecture

```text
Android phone camera
  ├─ Front camera
  └─ Rear camera
          │
          ├─ RTSP / HTTP-MJPEG over Wi-Fi or tethering
          └─ USB/UVC when supported by the phone
          ↓
MobileCam Bridge source backend
          ↓
Latest-frame queue + timestamp + metadata
          ↓
GUI / headless service / FrameProvider API
          ↓
OpenCV | GStreamer | AXON/RKNN | TI/TIDL | ADAS | DMS
```

## Current scope

Version `0.1.0` provides the host-side platform and the Android control contract. Camera switching depends on the Android streaming application.

Expected control request:

```http
POST /api/v1/camera
Content-Type: application/json

{"lens":"front"}
```

Supported values are `front` and `rear`. A future Android CameraX companion application can implement the same contract and provide RTSP/H.264 streaming.

## Installation

### Windows

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .
mobilecam-gui
```

The included launcher can also be used:

```powershell
scripts\run_gui_windows.bat
```

### Linux / Vicharak AXON

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e .
mobilecam-gui
```

Or:

```bash
chmod +x scripts/run_gui_linux.sh
./scripts/run_gui_linux.sh
```

### Install from the wheel

A Python wheel is available in `dist/`:

```bash
pip install dist/mobilecam_platform-0.1.0-py3-none-any.whl
mobilecam-gui
```

## Quick start with an Android RTSP stream

1. Connect the phone and host to the same network, or use USB/Wi-Fi tethering.
2. Start an Android camera application that exposes an RTSP or MJPEG URL.
3. Copy `configs/example_rtsp.yaml` and enter the phone stream and control URLs.
4. Start the GUI:

```bash
mobilecam-gui --config configs/example_rtsp.yaml
```

5. Select **Front** or **Rear**, then connect.

Example configuration:

```yaml
name: android-phone
source:
  kind: rtsp
  uri: rtsp://192.168.1.100:8554/camera
  width: 1280
  height: 720
  fps: 30
  reconnect_delay_s: 1.0
android_control:
  enabled: true
  base_url: http://192.168.1.100:8080
  camera_endpoint: /api/v1/camera
  timeout_s: 2.0
```

## USB/UVC mode

When the Android phone firmware supports USB webcam mode, connect it to the host and select the appropriate local camera device.

Linux discovery:

```bash
v4l2-ctl --list-devices
v4l2-ctl --device=/dev/video0 --list-formats-ext
```

Windows uses a DirectShow camera index or device exposed to OpenCV.

UVC mode may expose only one selected phone camera. Front/rear switching support depends on the phone firmware.

## Headless CLI

```bash
mobilecam --config configs/example_rtsp.yaml --preview
```

Run without preview for integration services:

```bash
mobilecam --config configs/example_rtsp.yaml
```

## Python integration API

```python
from mobilecam_platform.config import load_config
from mobilecam_platform.provider import FrameProvider

provider = FrameProvider(load_config("configs/example_rtsp.yaml"))
provider.start()

try:
    packet = provider.read(timeout_s=2.0)
    if packet is not None:
        frame = packet.frame
        timestamp_ns = packet.timestamp_ns
        metadata = packet.metadata
finally:
    provider.stop()
```

Downstream branches should depend on `FrameProvider`, not directly on OpenCV capture. This preserves portability across desktop and embedded targets.

## Target integration strategy

The `main` branch remains platform-neutral. Recommended derived branches are:

```text
integration/windows-opencv
integration/linux-gstreamer
integration/axon-rk3588
integration/ti-tidl
integration/advis-dms
integration/advis-forward
```

Target code should consume the common frame packet and add only target-specific decoding, memory movement and inference adapters.

## Repository layout

```text
mobilecam-bridge/
├── src/mobilecam_platform/       Core package, GUI, CLI and backends
├── configs/                      RTSP and UVC example profiles
├── android-companion/            Android control/streaming contract
├── docs/                         Integration guidance
├── scripts/                      Windows and Linux launchers
├── tests/                        Unit tests
├── dist/                         Installable Python artifacts
├── .github/workflows/            Cross-platform CI
├── pyproject.toml
└── README.md
```

## Platform notes

### Vicharak AXON / RK3588

Start with RTSP/H.264 or V4L2 capture. A target branch can later replace software decoding with Rockchip MPP/GStreamer and feed RKNN inference without changing the public frame-provider contract.

### TI Jacinto / TIDL

Use the host implementation for algorithm development. A TI branch can provide a GStreamer/TIOVX decoder and memory adapter that converts the selected phone stream into the tensor and buffer formats expected by TIDL.

### Windows and Linux

The default OpenCV backend supports rapid development and validation. GStreamer pipelines can be used where lower latency or hardware decoding is required.

## Limitations

- The project does not yet include a compiled Android APK.
- Front/rear selection requires support from the Android streaming application or future companion app.
- A single phone is not assumed to provide synchronized front and rear streams.
- Network streaming is not suitable for safety-critical latency or production camera validation.
- Phone image processing, auto exposure and stabilization can affect ADAS/DMS measurements.

## Development

```bash
pip install -e ".[dev]"
pytest
ruff check .
```

## Roadmap

- Android CameraX companion application
- H.264 RTSP server and camera-control service
- Device discovery and pairing
- Stream latency measurement
- Hardware decode adapters for RK3588 and TI Jacinto
- Optional dual-phone synchronization metadata
- Packaged Windows executable and Linux AppImage

## License

Apache License 2.0. See [LICENSE](LICENSE).
