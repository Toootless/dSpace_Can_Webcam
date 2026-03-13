#!/usr/bin/env python
"""
DSpace CAN Integration Application Demo - Webcam Edition
Runs application with fallback if no webcam available
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from main import DSpaceCANApplication

if __name__ == "__main__":
    # Try with webcam, but continue without it if not available
    print("=" * 70)
    print("DSpace CAN Integration with Webcam Support")
    print("=" * 70)
    
    app = DSpaceCANApplication(enable_webcam=True)
    app.run(duration=10.0)
    
    print("\n" + "=" * 70)
    print("Recording complete! Check recordings/ directory for output files")
    print("=" * 70)
