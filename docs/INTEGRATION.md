# Integration Guide

## Common contract

Downstream code consumes `FramePacket`, not phone-specific APIs. Each packet contains:

- `frame`: OpenCV BGR ndarray
- `timestamp_ns`: host monotonic capture timestamp
- `sequence`: increasing frame number
- `source_name`: profile name

This keeps perception code independent from Android, RTSP, UVC and target hardware.

## Windows

Use the FFmpeg backend for RTSP/MJPEG or DirectShow for UVC. Install the standard Python package and run `mobilecam-gui`.

## Linux

Use FFmpeg or GStreamer for network streams and V4L2 for UVC. Verify the camera with `v4l2-ctl --list-devices`.

## Vicharak AXON / RK3588

Recommended path:

1. Receive H.264 RTSP.
2. Decode using Rockchip MPP where available.
3. Convert to NV12/RGB only once.
4. Feed the frame to RKNN preprocessing.

The helper `build_gstreamer_pipeline(config.source, target="axon")` creates a starting pipeline. Exact plugin names depend on the AXON image.

## TI Jacinto / TIDL

Keep acquisition outside the model runner. Convert incoming frames into the tensor format expected by the TIDL application, preferably using GStreamer/TIOVX elements available in the TI Processor SDK.

Recommended branch structure later:

- `integration/windows-opencv`
- `integration/linux-gstreamer`
- `integration/axon-rk3588`
- `integration/ti-tidl`
- `integration/advis-dms`
- `integration/advis-forward`

## Latency policy

For live ADAS/DMS development, always use a latest-frame queue of one frame. Do not allow unbounded buffering. Measure capture age separately from inference time.
