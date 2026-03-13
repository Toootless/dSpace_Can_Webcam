# dSpace CAN + WebCam

A Python application that reads from **two CAN bus channels** simultaneously
and overlays the live data onto a **webcam video stream**, logging everything
to disk for dSpace HIL (Hardware-In-the-Loop) post-processing or replay.

---

## Features

| Feature | Detail |
|---|---|
| Dual CAN input | Two independent `python-can` buses running in background threads |
| WebCam capture | Any OpenCV-compatible USB or integrated camera |
| Live overlay | Latest CAN frames drawn on the video in real time |
| CSV logging | All CAN messages written to a timestamped CSV file |
| Video logging | Annotated video saved as MP4 |
| Clean shutdown | Handles `Ctrl-C` / `SIGTERM` gracefully |

---

## Project layout

```
.
├── main.py            # Entry point – starts all subsystems and runs the capture loop
├── config.py          # All tunable settings (CAN interface, camera index, log dir, …)
├── can_interface.py   # Thread-safe dual-CAN reader (wraps python-can)
├── webcam.py          # OpenCV VideoCapture wrapper
├── overlay.py         # Draws CAN data panel onto video frames
├── dspace_logger.py   # Writes CSV and MP4 log files
├── tests.py           # Unit tests (no hardware required)
└── requirements.txt   # Python dependencies
```

---

## Requirements

- Python ≥ 3.10
- A CAN adapter supported by [python-can](https://python-can.readthedocs.io/)
  (SocketCAN, PCAN, Kvaser, Vector, …)
- A webcam accessible by OpenCV

### Install dependencies

```bash
pip install -r requirements.txt
```

---

## Configuration

Edit `config.py` before running.  The most important settings are:

```python
# CAN
CAN_INTERFACE = "socketcan"   # e.g. 'pcan', 'kvaser', 'vector', 'virtual'
CAN_CHANNEL_1 = "can0"        # first  CAN channel
CAN_CHANNEL_2 = "can1"        # second CAN channel
CAN_BITRATE   = 500_000       # bits/second

# Camera
WEBCAM_INDEX  = 0             # 0 = first USB/built-in camera

# Logging
LOG_DIR       = "logs"        # output directory for CSV + video
LOG_CAN_CSV   = True
LOG_VIDEO     = True
SHOW_PREVIEW  = True          # display live OpenCV window
```

For testing **without physical hardware**, set `CAN_INTERFACE = "virtual"`.

---

## Usage

```bash
python main.py
```

- Press **q** or **Esc** in the preview window to stop.
- Press **Ctrl-C** in the terminal to stop.

Log files are written to the `logs/` directory with a timestamp in the filename:

```
logs/
├── can_20240101_120000.csv    # all CAN messages from both channels
└── video_20240101_120000.mp4  # annotated video
```

---

## Running tests

```bash
pip install pytest
python -m pytest tests.py -v
```

The tests use a `virtual` CAN interface and mock OpenCV – no hardware needed.

---

## CAN overlay example

```
── CAN Channel 1 ──
  ID:0x100  [8]  01 02 03 04 05 06 07 08
  ID:0x201  [3]  AA BB CC
── CAN Channel 2 ──
  ID:0x300  [4]  DE AD BE EF
```
