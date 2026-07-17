# Android Companion Contract

The host application is intentionally compatible with any Android app that provides:

1. A stable RTSP or HTTP/MJPEG stream URL.
2. A camera-selection HTTP endpoint.

## Required control endpoint

```http
POST /api/v1/camera
Content-Type: application/json

{"lens":"front"}
```

or

```json
{"lens":"rear"}
```

Expected response: HTTP 200 after the stream has switched or restarted.

## Recommended implementation

- Kotlin + CameraX
- `CameraSelector.DEFAULT_FRONT_CAMERA` / `DEFAULT_BACK_CAMERA`
- MediaCodec H.264 encoder
- Embedded RTSP server or WebRTC gateway
- Keep stream URL stable while switching lenses
- Return sensor orientation, resolution, FPS and active lens from `/api/v1/status`

A production companion app should also expose focus, exposure lock, torch, stabilization and bitrate controls. These controls are intentionally outside v0.1 of the host platform.
