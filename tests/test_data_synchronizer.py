"""
Unit tests for Data Synchronizer module
"""

import pytest
import tempfile
from pathlib import Path
from src.data_synchronizer import DataSynchronizer, SyncedData
import json


def test_data_synchronizer_initialization():
    """Test data synchronizer initialization"""
    with tempfile.TemporaryDirectory() as tmpdir:
        sync = DataSynchronizer(output_dir=tmpdir)
        assert sync.running == False
        assert len(sync.sync_data) == 0


def test_data_synchronizer_session_start():
    """Test session start"""
    with tempfile.TemporaryDirectory() as tmpdir:
        sync = DataSynchronizer(output_dir=tmpdir)
        sync.start_session("test_session")
        
        assert sync.running == True
        assert sync.session_name == "test_session"
        assert sync.session_started is not None


def test_data_synchronizer_add_can_message():
    """Test adding CAN messages"""
    with tempfile.TemporaryDirectory() as tmpdir:
        sync = DataSynchronizer(output_dir=tmpdir)
        sync.start_session()
        
        sync.add_can_message(0, 0x123, b'\x01\x02\x03', 1.0)
        assert len(sync.can_buffer) == 1
        
        message = sync.can_buffer[0]
        assert message["bus_id"] == 0
        assert message["message_id"] == "0x123"


def test_data_synchronizer_add_webcam_frame():
    """Test adding webcam frames"""
    with tempfile.TemporaryDirectory() as tmpdir:
        sync = DataSynchronizer(output_dir=tmpdir)
        sync.start_session()
        
        sync.add_webcam_frame(frame_number=1, timestamp=1.0)
        assert len(sync.webcam_buffer) == 1
        
        frame = sync.webcam_buffer[0]
        assert frame["frame_number"] == 1
        assert frame["timestamp"] == 1.0


def test_data_synchronizer_sync_data_point():
    """Test creating synchronized data points"""
    with tempfile.TemporaryDirectory() as tmpdir:
        sync = DataSynchronizer(output_dir=tmpdir)
        sync.start_session()
        
        # Add some messages
        sync.add_can_message(0, 0x100, b'\x01\x02', 1.0)
        sync.add_can_message(1, 0x200, b'\x03\x04', 1.1)
        
        # Create sync point
        sync.sync_data_point(timestamp=1.1, frame_number=1, webcam_frame_number=30)
        
        assert len(sync.sync_data) == 1
        assert sync.sync_data[0].frame_number == 1
        assert sync.sync_data[0].webcam_frame_number == 30
        assert len(sync.sync_data[0].can_messages) == 2


def test_data_synchronizer_get_statistics():
    """Test getting statistics"""
    with tempfile.TemporaryDirectory() as tmpdir:
        sync = DataSynchronizer(output_dir=tmpdir)
        sync.start_session("stats_test")
        
        sync.add_can_message(0, 0x100, b'\x01', 1.0)
        sync.sync_data_point(1.0, 1, 30)
        
        stats = sync.get_statistics()
        assert stats["running"] == True
        assert stats["session_name"] == "stats_test"


def test_data_synchronizer_stop_session():
    """Test stopping session and saving data"""
    with tempfile.TemporaryDirectory() as tmpdir:
        sync = DataSynchronizer(output_dir=tmpdir)
        sync.start_session("save_test")
        
        # Add some test data
        sync.add_can_message(0, 0x100, b'\x01\x02\x03', 1.0)
        sync.sync_data_point(1.0, 1, 30)
        
        # Stop and save
        summary = sync.stop_session()
        
        assert sync.running == False
        assert "session_name" in summary
        assert "total_sync_points" in summary
        assert summary["total_sync_points"] == 1
        
        # Verify files were created
        output_path = Path(tmpdir)
        sessions = list(output_path.glob("save_test_*"))
        assert len(sessions) > 0
