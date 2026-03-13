"""
CAN bus interface module.

Manages two independent python-can buses and exposes a thread-safe API for
reading the most-recently-received messages on each channel.
"""

from __future__ import annotations

import logging
import queue
import threading
from typing import List, Optional

import can

import config

logger = logging.getLogger(__name__)


class CANChannel:
    """Wraps a single python-can Bus and collects messages in a background thread."""

    def __init__(self, channel: str, interface: str, bitrate: int, buffer_size: int) -> None:
        self.channel = channel
        self.interface = interface
        self.bitrate = bitrate
        self.buffer_size = buffer_size

        self._bus: Optional[can.BusABC] = None
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._queue: queue.Queue[can.Message] = queue.Queue(maxsize=buffer_size)
        self._lock = threading.Lock()
        self._latest: List[can.Message] = []

    # ── Lifecycle ──────────────────────────────────────────────────────────────

    def start(self) -> None:
        """Open the CAN bus and start the background listener thread."""
        logger.info("Opening CAN channel '%s' on interface '%s' at %d bps",
                    self.channel, self.interface, self.bitrate)
        self._bus = can.interface.Bus(
            channel=self.channel,
            interface=self.interface,
            bitrate=self.bitrate,
        )
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._receive_loop,
            name=f"can-rx-{self.channel}",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        """Signal the listener thread to stop and close the bus."""
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
        if self._bus is not None:
            try:
                self._bus.shutdown()
            except Exception:  # pylint: disable=broad-except
                pass
        logger.info("CAN channel '%s' stopped.", self.channel)

    # ── Data access ───────────────────────────────────────────────────────────

    def get_latest_messages(self) -> List[can.Message]:
        """Return a snapshot of the most recently received messages."""
        with self._lock:
            return list(self._latest)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _receive_loop(self) -> None:
        """Blocking receive loop executed in the background thread."""
        assert self._bus is not None
        while not self._stop_event.is_set():
            try:
                msg = self._bus.recv(timeout=0.1)
            except can.CanError as exc:
                logger.error("CAN receive error on '%s': %s", self.channel, exc)
                continue
            if msg is None:
                continue
            with self._lock:
                self._latest.append(msg)
                if len(self._latest) > self.buffer_size:
                    self._latest = self._latest[-self.buffer_size :]
            try:
                self._queue.put_nowait(msg)
            except queue.Full:
                pass  # drop oldest if consumer is too slow


class CANInterface:
    """Manages both CAN channels defined in *config*."""

    def __init__(self) -> None:
        self.channel1 = CANChannel(
            channel=config.CAN_CHANNEL_1,
            interface=config.CAN_INTERFACE,
            bitrate=config.CAN_BITRATE,
            buffer_size=config.CAN_BUFFER_SIZE,
        )
        self.channel2 = CANChannel(
            channel=config.CAN_CHANNEL_2,
            interface=config.CAN_INTERFACE,
            bitrate=config.CAN_BITRATE,
            buffer_size=config.CAN_BUFFER_SIZE,
        )

    def start(self) -> None:
        """Open both CAN channels."""
        self.channel1.start()
        self.channel2.start()

    def stop(self) -> None:
        """Close both CAN channels."""
        self.channel1.stop()
        self.channel2.stop()

    def get_messages(self) -> tuple[List[can.Message], List[can.Message]]:
        """Return latest messages for (channel1, channel2)."""
        return (
            self.channel1.get_latest_messages(),
            self.channel2.get_latest_messages(),
        )
