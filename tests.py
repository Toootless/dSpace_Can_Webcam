"""
Unit and integration tests for the dSpace CAN + WebCam project.

These tests use a 'virtual' CAN interface (no physical hardware required)
and mock OpenCV to avoid needing a real camera.
"""

from __future__ import annotations

import time
import unittest
from unittest.mock import MagicMock, patch

import can
import numpy as np


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_msg(arb_id: int = 0x100, data: bytes = b"\x01\x02\x03") -> can.Message:
    return can.Message(
        arbitration_id=arb_id,
        data=data,
        is_extended_id=False,
        timestamp=time.time(),
    )


# ── CANChannel tests ──────────────────────────────────────────────────────────

class TestCANChannel(unittest.TestCase):
    """Tests for can_interface.CANChannel using the virtual bus."""

    def test_virtual_bus_start_stop(self) -> None:
        """CANChannel should open and close a virtual bus without errors."""
        from can_interface import CANChannel
        ch = CANChannel(
            channel="test_channel",
            interface="virtual",
            bitrate=500_000,
            buffer_size=10,
        )
        ch.start()
        self.assertIsNotNone(ch._bus)
        ch.stop()

    def test_messages_empty_on_start(self) -> None:
        """No messages should be present immediately after opening."""
        from can_interface import CANChannel
        ch = CANChannel(
            channel="test_channel_empty",
            interface="virtual",
            bitrate=500_000,
            buffer_size=10,
        )
        ch.start()
        msgs = ch.get_latest_messages()
        ch.stop()
        self.assertIsInstance(msgs, list)

    def test_buffer_does_not_exceed_size(self) -> None:
        """Internal buffer must never grow beyond *buffer_size*."""
        from can_interface import CANChannel
        ch = CANChannel(
            channel="test_channel_buf",
            interface="virtual",
            bitrate=500_000,
            buffer_size=5,
        )
        ch.start()
        # Send messages directly via a virtual sender
        sender = can.interface.Bus(channel="test_channel_buf", interface="virtual")
        for i in range(20):
            sender.send(_make_msg(arb_id=i))
        time.sleep(0.3)  # allow receiver thread to process
        msgs = ch.get_latest_messages()
        sender.shutdown()
        ch.stop()
        self.assertLessEqual(len(msgs), 5)


# ── CANInterface tests ────────────────────────────────────────────────────────

class TestCANInterface(unittest.TestCase):
    """Tests for can_interface.CANInterface."""

    @patch("can_interface.config")
    def test_start_stop_virtual(self, mock_cfg: MagicMock) -> None:
        """CANInterface should start and stop both channels."""
        mock_cfg.CAN_INTERFACE   = "virtual"
        mock_cfg.CAN_CHANNEL_1   = "ci_ch1"
        mock_cfg.CAN_CHANNEL_2   = "ci_ch2"
        mock_cfg.CAN_BITRATE     = 500_000
        mock_cfg.CAN_BUFFER_SIZE = 10
        from can_interface import CANInterface
        iface = CANInterface()
        iface.start()
        ch1, ch2 = iface.get_messages()
        self.assertIsInstance(ch1, list)
        self.assertIsInstance(ch2, list)
        iface.stop()


# ── Overlay tests ─────────────────────────────────────────────────────────────

class TestOverlay(unittest.TestCase):
    """Tests for overlay.draw_overlay."""

    def setUp(self) -> None:
        self.frame = np.zeros((480, 640, 3), dtype=np.uint8)

    def test_returns_ndarray(self) -> None:
        from overlay import draw_overlay
        result = draw_overlay(self.frame, [], [])
        self.assertIsInstance(result, np.ndarray)
        self.assertEqual(result.shape, self.frame.shape)

    def test_does_not_mutate_input(self) -> None:
        from overlay import draw_overlay
        original = self.frame.copy()
        draw_overlay(self.frame, [_make_msg()], [_make_msg(0x200)])
        np.testing.assert_array_equal(self.frame, original)

    def test_with_messages(self) -> None:
        from overlay import draw_overlay
        msgs1 = [_make_msg(0x100, b"\xAA\xBB")]
        msgs2 = [_make_msg(0x200, b"\xCC\xDD")]
        result = draw_overlay(self.frame, msgs1, msgs2)
        # The overlay should have modified at least some pixels
        self.assertFalse(np.all(result == 0))

    @patch("overlay.config")
    def test_overlay_disabled(self, mock_cfg: MagicMock) -> None:
        """When OVERLAY_CAN is False the original frame must be returned unchanged."""
        mock_cfg.OVERLAY_CAN = False
        from overlay import draw_overlay
        result = draw_overlay(self.frame, [_make_msg()], [_make_msg(0x200)])
        np.testing.assert_array_equal(result, self.frame)


# ── DataLogger tests ──────────────────────────────────────────────────────────

class TestDataLogger(unittest.TestCase):
    """Tests for dspace_logger.DataLogger."""

    def setUp(self) -> None:
        import tempfile
        import config as cfg
        self._tmpdir = tempfile.mkdtemp()
        cfg.LOG_DIR   = self._tmpdir
        cfg.LOG_CAN_CSV = True
        cfg.LOG_VIDEO   = False   # skip video writer in unit tests

    def test_open_creates_csv(self) -> None:
        import os
        from dspace_logger import DataLogger
        dl = DataLogger()
        dl.open(frame_width=320, frame_height=240)
        dl.close()
        csv_files = [f for f in os.listdir(self._tmpdir) if f.endswith(".csv")]
        self.assertEqual(len(csv_files), 1)

    def test_write_can_messages(self) -> None:
        import csv, os
        from dspace_logger import DataLogger
        dl = DataLogger()
        dl.open(frame_width=320, frame_height=240)
        dl.write_can_messages(1, [_make_msg(0x123, b"\xDE\xAD")])
        dl.write_can_messages(2, [_make_msg(0x456, b"\xBE\xEF")])
        dl.close()
        csv_file = next(
            f for f in os.listdir(self._tmpdir) if f.endswith(".csv")
        )
        with open(os.path.join(self._tmpdir, csv_file)) as fh:
            rows = list(csv.DictReader(fh))
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["channel"], "1")
        self.assertEqual(rows[1]["channel"], "2")


# ── WebCam tests ──────────────────────────────────────────────────────────────

class TestWebCam(unittest.TestCase):
    """Tests for webcam.WebCam using a mocked VideoCapture."""

    @patch("webcam.cv2.VideoCapture")
    def test_open_success(self, MockCap: MagicMock) -> None:
        mock_cap = MockCap.return_value
        mock_cap.isOpened.return_value = True
        mock_cap.get.return_value = 0

        from webcam import WebCam
        cam = WebCam()
        cam.open()
        self.assertTrue(cam.is_open)
        cam.release()

    @patch("webcam.cv2.VideoCapture")
    def test_open_failure_raises(self, MockCap: MagicMock) -> None:
        mock_cap = MockCap.return_value
        mock_cap.isOpened.return_value = False

        from webcam import WebCam
        cam = WebCam()
        with self.assertRaises(RuntimeError):
            cam.open()

    @patch("webcam.cv2.VideoCapture")
    def test_read_returns_frame(self, MockCap: MagicMock) -> None:
        mock_cap = MockCap.return_value
        mock_cap.isOpened.return_value = True
        mock_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_cap.read.return_value = (True, mock_frame)
        mock_cap.get.return_value = 0

        from webcam import WebCam
        cam = WebCam()
        cam.open()
        ok, frame = cam.read()
        self.assertTrue(ok)
        self.assertIsNotNone(frame)
        cam.release()

    @patch("webcam.cv2.VideoCapture")
    def test_read_without_open(self, _MockCap: MagicMock) -> None:
        from webcam import WebCam
        cam = WebCam()
        ok, frame = cam.read()
        self.assertFalse(ok)
        self.assertIsNone(frame)


if __name__ == "__main__":
    unittest.main()
