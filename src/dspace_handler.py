"""
DSpace Handler Module
Manages DSpace environment interactions for CAN data processing
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Optional import for DSpace client
try:
    from dspace_client import DSpaceAPI
except ImportError:
    logger.warning("dspace_client module not available, using mock API")
    DSpaceAPI = None


class DSpaceHandler:
    """Handles DSpace environment configuration and data management"""
    
    def __init__(self, base_url: str = "http://localhost:8080/rest"):
        """
        Initialize DSpace handler
        
        Args:
            base_url: DSpace REST API base URL
        """
        self.base_url = base_url
        self.api: Optional[Any] = None
        self.authenticated = False
        self.can_data_store = {
            "bus1_messages": [],
            "bus2_messages": [],
            "total_messages": 0
        }
    
    def connect(self, username: str, password: str) -> bool:
        """
        Connect to DSpace environment
        
        Args:
            username: DSpace username
            password: DSpace password
            
        Returns:
            bool: Connection success status
        """
        try:
            logger.info(f"Connecting to DSpace at {self.base_url}")
            # Initialize DSpace API client if available
            if DSpaceAPI is not None:
                self.api = DSpaceAPI(self.base_url)
            else:
                logger.info("Using mock DSpace API (dspace_client not available)")
                self.api = None
            # Authentication would occur here
            self.authenticated = True
            logger.info("Successfully connected to DSpace")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to DSpace: {e}")
            return False
    
    def store_can_data(self, bus_id: int, message_id: int, data: bytes):
        """
        Store CAN message data in DSpace
        
        Args:
            bus_id: CAN bus identifier (0 or 1)
            message_id: CAN message ID
            data: Message data
        """
        if not self.authenticated:
            logger.warning("Not authenticated with DSpace")
            return
        
        try:
            if bus_id == 0:
                self.can_data_store["bus1_messages"].append({
                    "message_id": message_id,
                    "data": data.hex(),
                    "size": len(data)
                })
            elif bus_id == 1:
                self.can_data_store["bus2_messages"].append({
                    "message_id": message_id,
                    "data": data.hex(),
                    "size": len(data)
                })
            
            self.can_data_store["total_messages"] += 1
            logger.debug(f"Stored CAN message from bus {bus_id}")
        except Exception as e:
            logger.error(f"Error storing CAN data: {e}")
    
    def disconnect(self):
        """Disconnect from DSpace environment"""
        self.authenticated = False
        logger.info("Disconnected from DSpace")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get CAN data statistics"""
        return {
            "bus1_messages_count": len(self.can_data_store["bus1_messages"]),
            "bus2_messages_count": len(self.can_data_store["bus2_messages"]),
            "total_messages": self.can_data_store["total_messages"],
            "authenticated": self.authenticated
        }
