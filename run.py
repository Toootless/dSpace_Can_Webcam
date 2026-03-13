#!/usr/bin/env python
"""
DSpace CAN Integration Application Launcher
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from main import DSpaceCANApplication

if __name__ == "__main__":
    app = DSpaceCANApplication(enable_webcam=True)
    app.run(duration=10.0)
