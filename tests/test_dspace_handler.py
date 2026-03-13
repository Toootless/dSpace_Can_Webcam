"""
Unit tests for DSpace Handler module
"""

import pytest
from src.dspace_handler import DSpaceHandler


def test_dspace_handler_initialization():
    """Test DSpace handler initialization"""
    handler = DSpaceHandler()
    assert handler.authenticated == False
    assert handler.base_url == "http://localhost:8080/rest"
    assert handler.can_data_store["total_messages"] == 0


def test_store_can_data():
    """Test storing CAN data when authenticated"""
    handler = DSpaceHandler()
    handler.authenticated = True
    
    handler.store_can_data(0, 0x100, b'\x01\x02\x03\x04')
    handler.store_can_data(1, 0x200, b'\x05\x06\x07\x08')
    
    stats = handler.get_statistics()
    assert stats["bus1_messages_count"] == 1
    assert stats["bus2_messages_count"] == 1
    assert stats["total_messages"] == 2


def test_get_statistics():
    """Test getting statistics"""
    handler = DSpaceHandler()
    handler.authenticated = True
    
    stats = handler.get_statistics()
    assert "bus1_messages_count" in stats
    assert "bus2_messages_count" in stats
    assert "total_messages" in stats
    assert "authenticated" in stats
