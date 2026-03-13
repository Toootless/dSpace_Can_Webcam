"""
WebCam capture module.

Opens an OpenCV VideoCapture device and provides frames on demand.
"""

from __future__ import annotations

import logging
from typing import Optional, Tuple

import cv2
import numpy as np

import config

logger = logging.getLogger(__name__)

# Type alias
Frame = np.ndarray


class WebCam:
    """Thin wrapper around :class:`cv2.VideoCapture`."""

    def __init__(self) -> None:
        self._cap: Optional[cv2.VideoCapture] = None

    # ── Lifecycle ──────────────────────────────────────────────────────────────

    def open(self) -> None:
        """Open the webcam device specified in *config*."""
        logger.info(
            "Opening webcam index=%d  resolution=%dx%d  fps=%d",
            config.WEBCAM_INDEX,
            config.FRAME_WIDTH,
            config.FRAME_HEIGHT,
            config.FRAME_FPS,
        )
        cap = cv2.VideoCapture(config.WEBCAM_INDEX)
        if not cap.isOpened():
            raise RuntimeError(
                f"Cannot open webcam at index {config.WEBCAM_INDEX}. "
                "Check that a camera is connected and not in use by another process."
            )
        cap.set(cv2.CAP_PROP_FRAME_WIDTH,  config.FRAME_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
        cap.set(cv2.CAP_PROP_FPS,          config.FRAME_FPS)
        self._cap = cap

    def release(self) -> None:
        """Release the camera resource."""
        if self._cap is not None:
            self._cap.release()
            self._cap = None
        logger.info("WebCam released.")

    # ── Frame access ──────────────────────────────────────────────────────────

    def read(self) -> Tuple[bool, Optional[Frame]]:
        """
        Read the next frame.

        Returns
        -------
        (ok, frame)
            *ok* is ``True`` when a frame was successfully captured.
            *frame* is the BGR image array, or ``None`` on failure.
        """
        if self._cap is None:
            return False, None
        ok, frame = self._cap.read()
        return ok, (frame if ok else None)

    @property
    def is_open(self) -> bool:
        """``True`` if the capture device is open."""
        return self._cap is not None and self._cap.isOpened()

    @property
    def actual_width(self) -> int:
        """Actual frame width reported by the driver."""
        if self._cap is None:
            return 0
        return int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))

    @property
    def actual_height(self) -> int:
        """Actual frame height reported by the driver."""
        if self._cap is None:
            return 0
        return int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
