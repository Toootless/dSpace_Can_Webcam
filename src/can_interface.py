"""
CAN Bus Interface Module
Handles two high-speed CAN bus inputs for DSpace environment
"""

import threading
import logging
from dataclasses import dataclass
from typing import Callable, Optional

logger = logging.getLogger(__name__)


@dataclass
class CANMessage:
    """Represents a CAN message from the bus"""
    bus_id: int  # CAN bus identifier (0 or 1)
    message_id: int
    data: bytes
    timestamp: float


class CANInterface:
    """Manages communication with dual CAN buses for DSpace"""
    
    def __init__(self, bus1_bitrate: int = 500000, bus2_bitrate: int = 500000):
        """
        Initialize CAN interface with two bus channels
        
        Args:
            bus1_bitrate: CAN bus 1 bitrate (default 500kbps)
            bus2_bitrate: CAN bus 2 bitrate (default 500kbps)
        """
        self.bus1_bitrate = bus1_bitrate
        self.bus2_bitrate = bus2_bitrate
        self.running = False
        self.message_callbacks = []
        self.lock = threading.Lock()
        
    def register_callback(self, callback: Callable[[CANMessage], None]):
        """Register callback for incoming CAN messages"""
        with self.lock:
            self.message_callbacks.append(callback)
    
    def start(self):
        """Start listening to CAN buses"""
        self.running = True
        logger.info(f"Starting CAN interface - Bus1: {self.bus1_bitrate}bps, Bus2: {self.bus2_bitrate}bps")
        
    def stop(self):
        """Stop listening to CAN buses"""
        self.running = False
        logger.info("Stopping CAN interface")
    
    def process_message(self, message: CANMessage):
        """Process incoming CAN message and trigger callbacks"""
        with self.lock:
            for callback in self.message_callbacks:
                try:
                    callback(message)
                except Exception as e:
                    logger.error(f"Error in CAN message callback: {e}")
    
    def get_status(self) -> dict:
        """Get current CAN interface status"""
        return {
            "running": self.running,
            "bus1_bitrate": self.bus1_bitrate,
            "bus2_bitrate": self.bus2_bitrate,
            "callbacks_registered": len(self.message_callbacks)
        }
