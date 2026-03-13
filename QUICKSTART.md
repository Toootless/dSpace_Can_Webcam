# DSpace CAN Integration Project

Quick reference for the DSpace CAN Bus Integration project with dual CAN input handlers.

## Location

`C:\Users\johnj\OneDrive\Documents\VS_projects\dspace\`

## Quick Start

```bash
# Navigate to project
cd C:\Users\johnj\OneDrive\Documents\VS_projects\dspace

# Install dependencies
pip install -r requirements.txt

# Run main application (with webcam)
python run.py

# Run without webcam (5 second demo)
python run_demo.py

# Run tests
pytest tests/ -v
```

## Dual CAN Bus Architecture

**Key Features:**
- **Bus 1**: 500 kbps (configurable)
- **Bus 2**: 500 kbps (configurable)
- Message IDs alternate between buses (Bus1: 0x100, 0x102, ...; Bus2: 0x101, 0x103, ...)
- Independent callback handlers for each bus
- Thread-safe message processing with locks
- Separate bitrate and callback configuration

**Test Results:**
```
Latest run: 2026-03-13 11:46:39 UTC
Duration: 5 seconds
Bus 1 Messages: 10 (alternating IDs starting at 0x100)
Bus 2 Messages: 10 (alternating IDs starting at 0x101)
Total Sync Points: 5
Webcam Frames: 5 (simulated)
Status: ✅ SUCCESS
```

## File Locations

- **Source Code**: `src/`
  - `can_interface.py` - Dual bus handler with CANInterface class
  - `dspace_handler.py` - DSpace REST API integration
  - `webcam_interface.py` - Webcam capture and recording
  - `data_synchronizer.py` - CAN and frame synchronization
  - `main.py` - Application orchestrator

- **Tests**: `tests/` (20 tests, all passing)
  - `test_can_interface.py` - 4 tests for CAN
  - `test_dspace_handler.py` - 3 tests for DSpace
  - `test_webcam_interface.py` - 6 tests for webcam
  - `test_data_synchronizer.py` - 7 tests for sync

- **Configuration**: `config/settings.json`
  - CAN bitrates (can_bus1_bitrate, can_bus2_bitrate)
  - DSpace URL and credentials
  - Logging configuration

- **Output**: `recordings/` (created at runtime)
  - Video files (.avi)
  - Session JSON data (sync_data.json, summary.json)

## Launchers

- `run.py` - Main app (webcam enabled, 10 seconds)
- `run_demo.py` - Demo without webcam (5 seconds)
- `run_with_webcam.py` - Webcam enabled with fallback

## Python Path

Automatically configured in launcher scripts via:
```python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
```

## Dependencies (from requirements.txt)

- dspace-client==0.3.1
- autobox==0.4.0
- pytest==9.0.2
- python-can==4.3.1
- httpx==0.25.2
- pyjwt==2.12.0
- pydantic>=2.0.2
- opencv-python==4.8.1.78

## Custom Dual Bus Handler Example

```python
from src.can_interface import CANInterface, CANMessage

class MyBusHandler:
    def __init__(self):
        self.can = CANInterface(bus1_bitrate=500000, bus2_bitrate=250000)
    
    def on_message(self, msg: CANMessage):
        if msg.bus_id == 0:
            print(f"Bus 1: ID=0x{msg.message_id:03X}")
        else:
            print(f"Bus 2: ID=0x{msg.message_id:03X}")
    
    def run(self):
        self.can.register_callback(self.on_message)
        self.can.start()

handler = MyBusHandler()
handler.run()
```

## Test Execution

```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_can_interface.py -v

# With coverage
pytest tests/ --cov=src --cov-report=html
```

## Output Files

After running application:
```
recordings/dspace_can_webcam_session_TIMESTAMP/
├── summary.json          # Session summary
└── sync_data.json        # CAN + frame correlation
```

## VS Code Integration

- **Debug Configs**: `.vscode/launch.json`
  - Python: Main Application
  - Python: Demo (No Webcam)
  - Python: Run Tests
- **Settings**: `.vscode/settings.json`
  - Flake8 linting enabled
  - Pytest configured
  - Python files excluded
