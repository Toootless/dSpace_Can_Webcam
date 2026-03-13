#!/usr/bin/env python
"""
DSpace CAN Integration Application Demo - Without Webcam
Demonstrates CAN data recording and synchronization
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from main import DSpaceCANApplication

if __name__ == "__main__":
    print("=" * 70)
    print("DSpace CAN Integration - CAN Data Recording Demo")
    print("=" * 70)
    print("Running without webcam (no camera available)...")
    print()
    
    app = DSpaceCANApplication(enable_webcam=False)
    app.run(duration=5.0)
    
    print("\n" + "=" * 70)
    print("Recording complete! Check recordings/ directory for output files:")
    print("  - Sync data and session summary in JSON format")
    print("=" * 70)
