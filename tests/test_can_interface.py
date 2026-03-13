"""
Unit tests for CAN Interface module
"""

import pytest
from src.can_interface import CANInterface, CANMessage


def test_can_interface_initialization():
    """Test CAN interface initialization"""
    can_if = CANInterface(bus1_bitrate=500000, bus2_bitrate=250000)
    assert can_if.bus1_bitrate == 500000
    assert can_if.bus2_bitrate == 250000
    assert can_if.running == False


def test_can_interface_status():
    """Test CAN interface status"""
    can_if = CANInterface()
    status = can_if.get_status()
    assert status["running"] == False
    assert status["callbacks_registered"] == 0


def test_can_interface_callback_registration():
    """Test callback registration"""
    can_if = CANInterface()
    callback_called = []
    
    def test_callback(msg):
        callback_called.append(msg)
    
    can_if.register_callback(test_callback)
    assert len(can_if.message_callbacks) == 1
    
    # Test callback execution
    test_msg = CANMessage(
        bus_id=0,
        message_id=0x123,
        data=b'\x01\x02\x03',
        timestamp=0.0
    )
    can_if.process_message(test_msg)
    assert len(callback_called) == 1
    assert callback_called[0].message_id == 0x123


def test_can_message_creation():
    """Test CAN message creation"""
    msg = CANMessage(
        bus_id=1,
        message_id=0x456,
        data=b'\x11\x22\x33\x44',
        timestamp=123.456
    )
    assert msg.bus_id == 1
    assert msg.message_id == 0x456
    assert len(msg.data) == 4
    assert msg.timestamp == 123.456
