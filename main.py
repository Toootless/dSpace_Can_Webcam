"""
dSpace CAN + WebCam – main entry point.

Starts two CAN bus listeners, opens the webcam, overlays live CAN data on
each captured frame, optionally saves both streams to disk, and shows a
real-time preview window.

Usage
-----
    python main.py

Press **q** or **Esc** in the preview window (or Ctrl-C in the terminal)
to stop the program cleanly.
"""

from __future__ import annotations

import logging
import signal
import sys
import time

import cv2

import config
from can_interface import CANInterface
from dspace_logger import DataLogger
from overlay import draw_overlay
from webcam import WebCam

# ── Logging setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s – %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Run the dSpace CAN + WebCam loop."""

    # ── Initialise subsystems ──────────────────────────────────────────────────
    can_iface   = CANInterface()
    cam         = WebCam()
    data_logger = DataLogger()

    # Register signal handlers for clean shutdown on Ctrl-C / SIGTERM
    running = True

    def _shutdown(signum: int, frame: object) -> None:  # noqa: ARG001
        nonlocal running
        logger.info("Shutdown signal received (%d).", signum)
        running = False

    signal.signal(signal.SIGINT,  _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    try:
        # Open CAN buses
        try:
            can_iface.start()
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Failed to start CAN interface: %s", exc)
            logger.warning("Continuing without CAN data (use 'virtual' interface for testing).")

        # Open webcam
        try:
            cam.open()
        except RuntimeError as exc:
            logger.error("%s", exc)
            sys.exit(1)

        # Open log files
        data_logger.open(
            frame_width=cam.actual_width or config.FRAME_WIDTH,
            frame_height=cam.actual_height or config.FRAME_HEIGHT,
        )

        logger.info("Recording started. Press 'q' / Esc in the preview window to stop.")
        frame_count = 0
        t_start = time.monotonic()

        # ── Main capture loop ──────────────────────────────────────────────────
        while running:
            ok, frame = cam.read()
            if not ok or frame is None:
                logger.warning("Dropped frame %d.", frame_count)
                continue

            # Fetch latest CAN data
            ch1_msgs, ch2_msgs = can_iface.get_messages()

            # Log raw CAN messages
            data_logger.write_can_messages(1, ch1_msgs)
            data_logger.write_can_messages(2, ch2_msgs)

            # Annotate frame with CAN overlay
            annotated = draw_overlay(frame, ch1_msgs, ch2_msgs)

            # Log annotated video
            data_logger.write_frame(annotated)

            frame_count += 1

            # Show preview
            if config.SHOW_PREVIEW:
                cv2.imshow("dSpace CAN + WebCam", annotated)
                key = cv2.waitKey(1) & 0xFF
                if key in (ord("q"), 27):  # 'q' or Esc
                    logger.info("Quit key pressed.")
                    break

        # ── Shutdown ───────────────────────────────────────────────────────────
        elapsed = time.monotonic() - t_start
        logger.info(
            "Captured %d frames in %.1f s (%.1f fps).",
            frame_count,
            elapsed,
            frame_count / elapsed if elapsed > 0 else 0,
        )

    finally:
        can_iface.stop()
        cam.release()
        data_logger.close()
        if config.SHOW_PREVIEW:
            cv2.destroyAllWindows()
        logger.info("Shutdown complete.")


if __name__ == "__main__":
    main()
