"""
Main application entry point for DSpace CAN Integration
Coordinates CAN interface, webcam input, and DSpace environment
"""

import logging
import time
from can_interface import CANInterface, CANMessage
from dspace_handler import DSpaceHandler
from webcam_interface import WebcamInterface, WebcamRecorder
from data_synchronizer import DataSynchronizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DSpaceCANApplication:
    """Main application for DSpace CAN bus integration with webcam support"""
    
    def __init__(self, dspace_url: str = "http://localhost:8080/rest", enable_webcam: bool = True):
        """
        Initialize the application
        
        Args:
            dspace_url: DSpace REST API URL
            enable_webcam: Enable webcam input and recording
        """
        self.can_interface = CANInterface(bus1_bitrate=500000, bus2_bitrate=500000)
        self.dspace_handler = DSpaceHandler(base_url=dspace_url)
        self.message_count = 0
        
        # Webcam components
        self.enable_webcam = enable_webcam
        self.webcam = None
        self.recorder = None
        self.synchronizer = DataSynchronizer()
        
        if enable_webcam:
            self.webcam = WebcamInterface(camera_index=0, width=640, height=480, fps=30)
            self.recorder = WebcamRecorder(output_path="./recordings/webcam_feed.avi", 
                                          fps=30, width=640, height=480)
    
    def on_can_message(self, message: CANMessage):
        """
        Handle incoming CAN message
        
        Args:
            message: CANMessage object
        """
        self.message_count += 1
        logger.info(f"CAN Bus {message.bus_id} - ID: 0x{message.message_id:03X}, "
                   f"Data: {message.data.hex()}, Count: {self.message_count}")
        
        # Store data in DSpace
        self.dspace_handler.store_can_data(message.bus_id, message.message_id, message.data)
        
        # Store in synchronizer
        self.synchronizer.add_can_message(
            message.bus_id, 
            message.message_id, 
            message.data, 
            message.timestamp
        )
    
    def on_webcam_frame(self, frame):
        """
        Handle incoming webcam frame
        
        Args:
            frame: WebcamFrame object
        """
        # Record frame if recording is active
        if self.recorder and self.recorder.recording:
            self.recorder.write_frame(frame.frame)
        
        # Add frame to synchronizer
        self.synchronizer.add_webcam_frame(frame.frame_number, frame.timestamp)
        
        if frame.frame_number % 30 == 0:  # Log every 30 frames
            logger.debug(f"Webcam frame {frame.frame_number} - {frame.width}x{frame.height}")
    
    def setup(self):
        """Setup application components"""
        logger.info("Setting up DSpace CAN Integration application...")
        
        # Register CAN message callback
        self.can_interface.register_callback(self.on_can_message)
        
        # Setup webcam if enabled
        if self.enable_webcam and self.webcam:
            if self.webcam.initialize():
                self.webcam.register_callback(self.on_webcam_frame)
                logger.info("Webcam initialized successfully")
            else:
                logger.warning("Failed to initialize webcam, continuing without it")
                self.enable_webcam = False
        
        # Connect to DSpace (would use actual credentials in production)
        if self.dspace_handler.connect("admin", "admin_password"):
            logger.info("DSpace connection established")
        else:
            logger.error("Failed to establish DSpace connection")
            return False
        
        return True
    
    def run(self, duration: float = 10.0):
        """
        Run the application for specified duration
        
        Args:
            duration: Run duration in seconds
        """
        if not self.setup():
            logger.error("Application setup failed")
            return
        
        try:
            logger.info(f"Starting CAN monitoring and recording for {duration} seconds...")
            
            # Start recording session
            self.synchronizer.start_session("dspace_can_webcam_session")
            
            # Start webcam recording if enabled
            if self.enable_webcam and self.recorder:
                if self.recorder.start_recording():
                    logger.info("Webcam recording started")
                else:
                    logger.warning("Failed to start webcam recording")
            
            self.can_interface.start()
            if self.enable_webcam and self.webcam:
                self.webcam.start()
            
            # Simulate CAN messages and sync with webcam frames
            start_time = time.time()
            message_id = 0x100
            frame_sync_counter = 0
            
            while time.time() - start_time < duration:
                # Simulate CAN Bus 1 message
                msg1 = CANMessage(
                    bus_id=0,
                    message_id=message_id,
                    data=b'\x01\x02\x03\x04\x05\x06\x07\x08',
                    timestamp=time.time() - start_time
                )
                self.can_interface.process_message(msg1)
                
                # Simulate CAN Bus 2 message
                msg2 = CANMessage(
                    bus_id=1,
                    message_id=message_id + 1,
                    data=b'\x08\x07\x06\x05\x04\x03\x02\x01',
                    timestamp=time.time() - start_time
                )
                self.can_interface.process_message(msg2)
                
                message_id += 2
                frame_sync_counter += 1
                
                # Sync data at regular intervals (every 2 message pairs)
                if frame_sync_counter % 2 == 0:
                    self.synchronizer.sync_data_point(
                        time.time() - start_time,
                        frame_sync_counter,
                        frame_sync_counter * 30  # Simulated webcam frame count
                    )
                
                time.sleep(0.5)  # 500ms between message pairs
            
        except KeyboardInterrupt:
            logger.info("Application interrupted by user")
        except Exception as e:
            logger.error(f"Error during application run: {e}")
        finally:
            self.shutdown()
    
    
    def shutdown(self):
        """Gracefully shutdown application"""
        logger.info("Shutting down application...")
        self.can_interface.stop()
        
        # Stop webcam and recording
        if self.enable_webcam and self.webcam:
            self.webcam.stop()
            self.webcam.release()
        
        if self.recorder:
            self.recorder.stop_recording()
        
        # Stop DSpace connection
        self.dspace_handler.disconnect()
        
        # Save synchronized recording session
        session_summary = self.synchronizer.stop_session()
        
        # Print final statistics
        stats = self.dspace_handler.get_statistics()
        logger.info(f"Final Statistics: {stats}")
        logger.info(f"Session Summary: {session_summary}")


if __name__ == "__main__":
    app = DSpaceCANApplication()
    app.run(duration=10.0)
