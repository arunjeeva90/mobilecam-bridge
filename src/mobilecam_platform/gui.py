from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import cv2
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from .android_control import AndroidCameraController
from .config import AppConfig, load_config
from .provider import FramePacket, FrameProvider


class MainWindow(QMainWindow):
    def __init__(self, config_path: str):
        super().__init__()
        self.setWindowTitle("MobileCam Bridge")
        self.resize(1100, 760)
        self.config_path = config_path
        self.config: AppConfig = load_config(config_path)
        self.provider: FrameProvider | None = None
        self.controller = AndroidCameraController(self.config.android_control)
        self.latest: FramePacket | None = None
        self.last_frame_time = 0.0
        self.measured_fps = 0.0
        self.recording = False
        self.writer: cv2.VideoWriter | None = None

        self.preview = QLabel("Disconnected")
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setMinimumSize(640, 360)
        self.preview.setStyleSheet("background:#111; color:#ddd;")

        self.uri = QLineEdit(self.config.source.uri)
        self.kind = QComboBox()
        self.kind.addItems(["rtsp", "http", "uvc", "device"])
        self.kind.setCurrentText(self.config.source.kind)
        self.lens = QComboBox()
        self.lens.addItems(["Rear", "Front"])
        self.width = QSpinBox()
        self.width.setRange(160, 7680)
        self.width.setValue(self.config.source.width)
        self.height = QSpinBox()
        self.height.setRange(120, 4320)
        self.height.setValue(self.config.source.height)
        self.fps = QSpinBox()
        self.fps.setRange(1, 240)
        self.fps.setValue(self.config.source.fps)
        self.status = QLabel("Ready")

        connect = QPushButton("Connect")
        connect.clicked.connect(self.connect_source)
        disconnect = QPushButton("Disconnect")
        disconnect.clicked.connect(self.disconnect_source)
        switch = QPushButton("Apply Camera")
        switch.clicked.connect(self.switch_camera)
        snapshot = QPushButton("Snapshot")
        snapshot.clicked.connect(self.save_snapshot)
        record = QPushButton("Start/Stop Recording")
        record.clicked.connect(self.toggle_record)
        load = QPushButton("Load Profile")
        load.clicked.connect(self.load_profile)

        form = QFormLayout()
        form.addRow("Source type", self.kind)
        form.addRow("URI / device", self.uri)
        form.addRow("Android camera", self.lens)
        form.addRow("Width", self.width)
        form.addRow("Height", self.height)
        form.addRow("Requested FPS", self.fps)

        buttons = QHBoxLayout()
        for button in (connect, disconnect, switch, snapshot, record, load):
            buttons.addWidget(button)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addLayout(buttons)
        layout.addWidget(self.preview, 1)
        layout.addWidget(self.status)
        root = QWidget()
        root.setLayout(layout)
        self.setCentralWidget(root)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(15)

    def connect_source(self) -> None:
        self.disconnect_source()
        self.config.source.kind = self.kind.currentText()
        self.config.source.uri = self.uri.text().strip()
        self.config.source.width = self.width.value()
        self.config.source.height = self.height.value()
        self.config.source.fps = self.fps.value()
        self.provider = FrameProvider(self.config)
        self.provider.start()
        self.status.setText("Connecting…")

    def disconnect_source(self) -> None:
        if self.provider:
            self.provider.stop()
        self.provider = None
        self.close_writer()
        self.status.setText("Disconnected")

    def switch_camera(self) -> None:
        lens = self.lens.currentText().lower()
        try:
            self.controller.switch(lens)
            self.status.setText(f"Android camera switched to {lens}")
        except Exception as exc:
            QMessageBox.warning(self, "Camera switch failed", str(exc))

    def refresh(self) -> None:
        if not self.provider:
            return
        packet = self.provider.read(timeout_s=0.001)
        if packet is None:
            if self.provider.last_error:
                self.status.setText(f"Reconnecting: {self.provider.last_error}")
            return
        now = time.monotonic()
        if self.last_frame_time:
            instant = 1.0 / max(now - self.last_frame_time, 1e-6)
            self.measured_fps = (
                instant if self.measured_fps == 0 else 0.9 * self.measured_fps + 0.1 * instant
            )
        self.last_frame_time = now
        self.latest = packet
        frame = packet.frame
        if self.recording:
            self.write_frame(frame)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, channels = rgb.shape
        image = QImage(rgb.data, w, h, channels * w, QImage.Format_RGB888).copy()
        pixmap = QPixmap.fromImage(image).scaled(
            self.preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.preview.setPixmap(pixmap)
        age_ms = (time.monotonic_ns() - packet.timestamp_ns) / 1e6
        self.status.setText(
            f"Connected | frame {packet.sequence} | {self.measured_fps:.1f} FPS | age {age_ms:.1f} ms"
        )

    def save_snapshot(self) -> None:
        if not self.latest:
            return
        directory = Path(self.config.output.snapshot_directory)
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"snapshot_{time.strftime('%Y%m%d_%H%M%S')}.jpg"
        cv2.imwrite(str(path), self.latest.frame)
        self.status.setText(f"Saved {path}")

    def toggle_record(self) -> None:
        self.recording = not self.recording
        if not self.recording:
            self.close_writer()
        self.status.setText("Recording" if self.recording else "Recording stopped")

    def write_frame(self, frame) -> None:
        if self.writer is None:
            directory = Path(self.config.output.record_directory)
            directory.mkdir(parents=True, exist_ok=True)
            path = directory / f"mobilecam_{time.strftime('%Y%m%d_%H%M%S')}.mp4"
            h, w = frame.shape[:2]
            self.writer = cv2.VideoWriter(
                str(path), cv2.VideoWriter_fourcc(*"mp4v"), max(self.fps.value(), 1), (w, h)
            )
        self.writer.write(frame)

    def close_writer(self) -> None:
        if self.writer:
            self.writer.release()
        self.writer = None
        self.recording = False

    def load_profile(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Load MobileCam profile", "configs", "YAML (*.yaml *.yml)"
        )
        if path:
            self.config = load_config(path)
            self.config_path = path
            self.controller = AndroidCameraController(self.config.android_control)
            self.uri.setText(self.config.source.uri)
            self.kind.setCurrentText(self.config.source.kind)
            self.width.setValue(self.config.source.width)
            self.height.setValue(self.config.source.height)
            self.fps.setValue(self.config.source.fps)

    def closeEvent(self, event) -> None:  # noqa: N802
        self.disconnect_source()
        event.accept()


def main() -> None:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--config", default="configs/example_rtsp.yaml")
    args, qt_args = parser.parse_known_args()
    app = QApplication([sys.argv[0], *qt_args])
    window = MainWindow(args.config)
    window.show()
    raise SystemExit(app.exec())


if __name__ == "__main__":
    main()
