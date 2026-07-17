from __future__ import annotations

import argparse
import time

import cv2

from .config import load_config
from .provider import FrameProvider


def main() -> None:
    parser = argparse.ArgumentParser(description="Android phone camera bridge")
    parser.add_argument("--config", default="configs/example_rtsp.yaml")
    parser.add_argument("--preview", action="store_true")
    args = parser.parse_args()

    provider = FrameProvider(load_config(args.config))
    provider.start()
    try:
        while True:
            packet = provider.read(timeout_s=2.0)
            if packet is None:
                print(f"Waiting for stream: {provider.last_error or 'no frame'}")
                continue
            if args.preview:
                cv2.imshow("MobileCam", packet.frame)
                if cv2.waitKey(1) & 0xFF in {27, ord('q')}:
                    break
            else:
                print(packet.sequence, packet.frame.shape, packet.timestamp_ns)
                time.sleep(0.05)
    except KeyboardInterrupt:
        pass
    finally:
        provider.stop()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
