"""
Data Synchronization Module
Synchronizes CAN stream with webcam video recording
"""

import logging
import json
import threading
from pathlib import Path
from typing import Dict, Any, List
from dataclasses import dataclass, asdict
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class SyncedData:
    """Container for synchronized CAN and webcam data"""
    timestamp: float
    frame_number: int
    can_messages: List[Dict[str, Any]]
    webcam_frame_number: int


class DataSynchronizer:
    """Synchronizes and records CAN data with webcam frames"""
    
    def __init__(self, output_dir: str = "./recordings"):
        """
        Initialize data synchronizer
        
        Args:
            output_dir: Output directory for recordings
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.running = False
        self.lock = threading.Lock()
        
        # Buffers for synchronization
        self.can_buffer: List[Dict] = []
        self.webcam_buffer: List[int] = []
        
        # Recording data
        self.sync_data: List[SyncedData] = []
        self.session_started = None
        self.session_name = "session"
    
    def start_session(self, session_name: str = "dspace_can_session"):
        """
        Start a new recording session
        
        Args:
            session_name: Name of the session
        """
        self.session_name = session_name
        self.session_started = datetime.now()
        self.running = True
        self.can_buffer.clear()
        self.webcam_buffer.clear()
        self.sync_data.clear()
        logger.info(f"Started recording session: {session_name}")
    
    def add_can_message(self, bus_id: int, message_id: int, data: bytes, timestamp: float):
        """
        Add CAN message to buffer
        
        Args:
            bus_id: CAN bus identifier
            message_id: CAN message ID
            data: Message data
            timestamp: Message timestamp
        """
        if not self.running:
            return
        
        with self.lock:
            message = {
                "bus_id": bus_id,
                "message_id": f"0x{message_id:03X}",
                "data": data.hex(),
                "timestamp": timestamp,
                "size": len(data)
            }
            self.can_buffer.append(message)
    
    def add_webcam_frame(self, frame_number: int, timestamp: float):
        """
        Add webcam frame reference to buffer
        
        Args:
            frame_number: Frame number
            timestamp: Frame timestamp
        """
        if not self.running:
            return
        
        with self.lock:
            self.webcam_buffer.append({
                "frame_number": frame_number,
                "timestamp": timestamp
            })
    
    def sync_data_point(self, timestamp: float, frame_number: int, webcam_frame_number: int):
        """
        Create a synchronized data point
        
        Args:
            timestamp: Timestamp for this sync point
            frame_number: Sequential frame number
            webcam_frame_number: Corresponding webcam frame number
        """
        if not self.running:
            return
        
        with self.lock:
            # Get CAN messages since last sync
            can_messages = self.can_buffer.copy()
            self.can_buffer.clear()
            
            synced = SyncedData(
                timestamp=timestamp,
                frame_number=frame_number,
                can_messages=can_messages,
                webcam_frame_number=webcam_frame_number
            )
            self.sync_data.append(synced)
    
    def stop_session(self) -> Dict[str, Any]:
        """
        Stop recording session and save data
        
        Returns:
            dict: Session summary
        """
        self.running = False
        
        summary = self._save_session_data()
        logger.info(f"Session saved: {summary}")
        return summary
    
    def _save_session_data(self) -> Dict[str, Any]:
        """
        Save session data to files
        
        Returns:
            dict: Save summary
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_dir = self.output_dir / f"{self.session_name}_{timestamp}"
        session_dir.mkdir(parents=True, exist_ok=True)
        
        # Save sync data
        sync_file = session_dir / "sync_data.json"
        sync_data_list = []
        
        for sync_point in self.sync_data:
            sync_data_list.append({
                "timestamp": sync_point.timestamp,
                "frame_number": sync_point.frame_number,
                "webcam_frame_number": sync_point.webcam_frame_number,
                "can_message_count": len(sync_point.can_messages),
                "can_messages": sync_point.can_messages
            })
        
        with open(sync_file, 'w') as f:
            json.dump(sync_data_list, f, indent=2)
        
        # Save summary
        summary_file = session_dir / "summary.json"
        summary = {
            "session_name": self.session_name,
            "session_started": self.session_started.isoformat() if self.session_started else None,
            "session_ended": datetime.now().isoformat(),
            "total_sync_points": len(self.sync_data),
            "total_can_messages": sum(len(s.can_messages) for s in self.sync_data),
            "total_webcam_frames": sum(1 for s in self.sync_data),
            "output_directory": str(session_dir)
        }
        
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Session data saved to {session_dir}")
        return summary
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get current session statistics"""
        return {
            "running": self.running,
            "session_name": self.session_name,
            "session_started": self.session_started.isoformat() if self.session_started else None,
            "buffered_can_messages": len(self.can_buffer),
            "sync_points": len(self.sync_data),
            "total_recorded_messages": sum(len(s.can_messages) for s in self.sync_data)
        }
