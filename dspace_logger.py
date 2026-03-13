"""
dSpace data-logging interface.

Writes timestamped CAN messages to a CSV file and annotated video to a file,
mirroring data that would be fed into a dSpace HIL (Hardware-In-the-Loop)
environment for post-processing or replay.
"""

from __future__ import annotations

import csv
import datetime
import logging
import os
import pathlib
from typing import List, Optional

import can
import cv2
import numpy as np

import config

logger = logging.getLogger(__name__)


def _timestamp() -> str:
    """Return a filesystem-safe ISO-8601 timestamp string."""
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


class DataLogger:
    """
    Logs CAN data (CSV) and annotated webcam frames (video) for dSpace replay.

    Usage::

        logger = DataLogger()
        logger.open()
        …
        logger.write_can_messages(1, messages_ch1)
        logger.write_can_messages(2, messages_ch2)
        logger.write_frame(frame)
        …
        logger.close()
    """

    def __init__(self) -> None:
        self._log_dir = pathlib.Path(config.LOG_DIR)
        self._session_id = _timestamp()

        self._csv_file  = None
        self._csv_writer: Optional[csv.DictWriter] = None
        self._video_writer: Optional[cv2.VideoWriter] = None
        self._frame_size: Optional[tuple[int, int]] = None

    # ── Lifecycle ──────────────────────────────────────────────────────────────

    def open(self, frame_width: int = config.FRAME_WIDTH,
             frame_height: int = config.FRAME_HEIGHT) -> None:
        """Create log files for this session."""
        self._log_dir.mkdir(parents=True, exist_ok=True)
        self._frame_size = (frame_width, frame_height)

        try:
            if config.LOG_CAN_CSV:
                csv_path = self._log_dir / f"can_{self._session_id}.csv"
                self._csv_file = open(csv_path, "w", newline="", encoding="utf-8")  # noqa: WPS515
                self._csv_writer = csv.DictWriter(
                    self._csv_file,
                    fieldnames=["timestamp", "channel", "arbitration_id",
                                 "dlc", "data", "is_extended_id", "is_remote_frame"],
                )
                self._csv_writer.writeheader()
                logger.info("CAN CSV log: %s", csv_path)

            if config.LOG_VIDEO:
                video_path = self._log_dir / f"video_{self._session_id}{config.VIDEO_EXT}"
                fourcc = cv2.VideoWriter_fourcc(*config.VIDEO_CODEC)
                self._video_writer = cv2.VideoWriter(
                    str(video_path), fourcc, config.FRAME_FPS, self._frame_size
                )
                logger.info("Video log: %s", video_path)
        except Exception:
            self.close()
            raise

    def close(self) -> None:
        """Flush and close all log files."""
        if self._csv_file is not None:
            self._csv_file.close()
            self._csv_file = None
        if self._video_writer is not None:
            self._video_writer.release()
            self._video_writer = None
        logger.info("DataLogger closed.")

    # ── Write helpers ─────────────────────────────────────────────────────────

    def write_can_messages(self, channel_number: int,
                           messages: List[can.Message]) -> None:
        """Append *messages* from the given CAN channel to the CSV file."""
        if self._csv_writer is None:
            return
        for msg in messages:
            self._csv_writer.writerow({
                "timestamp":       msg.timestamp,
                "channel":         channel_number,
                "arbitration_id":  f"0x{msg.arbitration_id:08X}",
                "dlc":             msg.dlc,
                "data":            msg.data.hex(),
                "is_extended_id":  msg.is_extended_id,
                "is_remote_frame": msg.is_remote_frame,
            })

    def write_frame(self, frame: np.ndarray) -> None:
        """Write a single video frame to the output file."""
        if self._video_writer is None:
            return
        if self._frame_size is not None:
            h, w = frame.shape[:2]
            if (w, h) != self._frame_size:
                frame = cv2.resize(frame, self._frame_size)
        self._video_writer.write(frame)
