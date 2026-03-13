"""
Unit tests for Webcam Interface module
"""

import pytest
from src.webcam_interface import WebcamInterface, WebcamFrame, WebcamRecorder
from pathlib import Path
import tempfile


def test_webcam_interface_initialization():
    """Test webcam interface initialization"""
    webcam = WebcamInterface(camera_index=0, width=640, height=480, fps=30)
    assert webcam.camera_index == 0
    assert webcam.width == 640
    assert webcam.height == 480
    assert webcam.fps == 30
    assert webcam.running == False


def test_webcam_frame_creation():
    """Test webcam frame creation"""
    import numpy as np
    frame_data = np.zeros((480, 640, 3), dtype=np.uint8)
    
    frame = WebcamFrame(
        frame=frame_data,
        timestamp=1.5,
        frame_number=42,
        width=640,
        height=480
    )
    
    assert frame.frame_number == 42
    assert frame.timestamp == 1.5
    assert frame.width == 640
    assert frame.height == 480


def test_webcam_interface_callback_registration():
    """Test callback registration"""
    webcam = WebcamInterface()
    callback_called = []
    
    def test_callback(frame):
        callback_called.append(frame.frame_number)
    
    webcam.register_callback(test_callback)
    assert len(webcam.frame_callbacks) == 1


def test_webcam_recorder_initialization():
    """Test webcam recorder initialization"""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_video.avi"
        recorder = WebcamRecorder(str(output_path), fps=30, width=640, height=480)
        
        assert recorder.fps == 30
        assert recorder.width == 640
        assert recorder.height == 480
        assert recorder.recording == False


def test_webcam_recorder_status():
    """Test recorder status"""
    recorder = WebcamRecorder()
    status = recorder.get_status()
    
    assert "recording" in status
    assert "fps" in status
    assert "resolution" in status
    assert status["recording"] == False


def test_webcam_interface_status():
    """Test webcam interface status"""
    webcam = WebcamInterface()
    status = webcam.get_status()
    
    assert status["running"] == False
    assert status["frame_count"] == 0
    assert status["camera_index"] == 0
