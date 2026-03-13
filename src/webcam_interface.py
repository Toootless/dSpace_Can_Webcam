"""
Webcam Interface Module
Handles webcam input and video streaming for data synchronization
"""

import cv2
import logging
import threading
import time
from dataclasses import dataclass
from typing import Callable, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class WebcamFrame:
    """Represents a webcam frame with timestamp"""
    frame: object  # OpenCV frame
    timestamp: float
    frame_number: int
    width: int
    height: int


class WebcamInterface:
    """Manages webcam input and video recording"""
    
    def __init__(self, camera_index: int = 0, width: int = 640, height: int = 480, fps: int = 30):
        """
        Initialize webcam interface
        
        Args:
            camera_index: Camera device index (default 0)
            width: Frame width
            height: Frame height
            fps: Frames per second
        """
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self.fps = fps
        self.cap = None
        self.running = False
        self.frame_count = 0
        self.frame_callbacks = []
        self.lock = threading.Lock()
        self.start_time = None
        
    def initialize(self) -> bool:
        """
        Initialize webcam capture
        
        Returns:
            bool: Initialization success status
        """
        try:
            self.cap = cv2.VideoCapture(self.camera_index)
            
            if not self.cap.isOpened():
                logger.error(f"Failed to open camera {self.camera_index}")
                return False
            
            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)
            
            logger.info(f"Webcam initialized - {self.width}x{self.height}@{self.fps}fps")
            return True
        except Exception as e:
            logger.error(f"Error initializing webcam: {e}")
            return False
    
    def start(self):
        """Start webcam capture thread"""
        if self.cap is None:
            logger.error("Webcam not initialized")
            return
        
        self.running = True
        self.start_time = time.time()
        self.frame_count = 0
        logger.info("Starting webcam capture")
        
        # Start capture thread
        capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        capture_thread.start()
    
    def _capture_loop(self):
        """Internal capture loop running in separate thread"""
        while self.running:
            try:
                ret, frame = self.cap.read()
                
                if not ret:
                    logger.warning("Failed to read frame from webcam")
                    break
                
                self.frame_count += 1
                timestamp = time.time() - self.start_time if self.start_time else 0
                
                webcam_frame = WebcamFrame(
                    frame=frame,
                    timestamp=timestamp,
                    frame_number=self.frame_count,
                    width=self.width,
                    height=self.height
                )
                
                self._trigger_callbacks(webcam_frame)
                
                # Control frame rate
                time.sleep(1.0 / self.fps)
                
            except Exception as e:
                logger.error(f"Error in capture loop: {e}")
                break
    
    def stop(self):
        """Stop webcam capture"""
        self.running = False
        logger.info("Stopping webcam capture")
    
    def register_callback(self, callback: Callable[[WebcamFrame], None]):
        """Register callback for new frames"""
        with self.lock:
            self.frame_callbacks.append(callback)
    
    def _trigger_callbacks(self, frame: WebcamFrame):
        """Trigger registered callbacks"""
        with self.lock:
            for callback in self.frame_callbacks:
                try:
                    callback(frame)
                except Exception as e:
                    logger.error(f"Error in webcam callback: {e}")
    
    def release(self):
        """Release webcam resources"""
        if self.cap:
            self.cap.release()
            logger.info("Webcam released")
    
    def get_status(self) -> dict:
        """Get webcam status"""
        return {
            "running": self.running,
            "frame_count": self.frame_count,
            "camera_index": self.camera_index,
            "resolution": f"{self.width}x{self.height}",
            "fps": self.fps
        }


class WebcamRecorder:
    """Records webcam video to file"""
    
    def __init__(self, output_path: str = "webcam_recording.avi", fps: int = 30, 
                 width: int = 640, height: int = 480):
        """
        Initialize video recorder
        
        Args:
            output_path: Output video file path
            fps: Frames per second
            width: Frame width
            height: Frame height
        """
        self.output_path = Path(output_path)
        self.fps = fps
        self.width = width
        self.height = height
        self.writer = None
        self.recording = False
        self.frame_count = 0
    
    def start_recording(self) -> bool:
        """
        Start recording video
        
        Returns:
            bool: Recording start success status
        """
        try:
            # Create output directory if needed
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Initialize video writer
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            self.writer = cv2.VideoWriter(
                str(self.output_path),
                fourcc,
                self.fps,
                (self.width, self.height)
            )
            
            if not self.writer.isOpened():
                logger.error(f"Failed to open video writer for {self.output_path}")
                return False
            
            self.recording = True
            self.frame_count = 0
            logger.info(f"Started recording video to {self.output_path}")
            return True
        except Exception as e:
            logger.error(f"Error starting video recording: {e}")
            return False
    
    def write_frame(self, frame):
        """
        Write frame to video file
        
        Args:
            frame: OpenCV frame
        """
        if self.recording and self.writer:
            try:
                self.writer.write(frame)
                self.frame_count += 1
            except Exception as e:
                logger.error(f"Error writing frame: {e}")
    
    def stop_recording(self):
        """Stop recording video"""
        if self.writer:
            self.writer.release()
            self.recording = False
            logger.info(f"Stopped recording video. Total frames: {self.frame_count}")
    
    def get_status(self) -> dict:
        """Get recording status"""
        return {
            "recording": self.recording,
            "output_path": str(self.output_path),
            "frames_written": self.frame_count,
            "fps": self.fps,
            "resolution": f"{self.width}x{self.height}"
        }
