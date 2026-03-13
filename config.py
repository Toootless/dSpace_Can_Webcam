"""
Configuration settings for the dSpace CAN + WebCam program.

Adjust these settings to match your hardware setup.
"""

# ── CAN Bus Configuration ─────────────────────────────────────────────────────

# Supported interfaces: 'socketcan', 'pcan', 'kvaser', 'vector', 'virtual', …
# Use 'virtual' for testing without physical hardware.
CAN_INTERFACE = "socketcan"

CAN_CHANNEL_1 = "can0"   # First  CAN channel (e.g. 'can0', 'PCAN_USBBUS1')
CAN_CHANNEL_2 = "can1"   # Second CAN channel (e.g. 'can1', 'PCAN_USBBUS2')

CAN_BITRATE   = 500_000  # Bits per second (500 kbit/s is common in automotive)

# How many CAN messages to keep in the rolling buffer per channel
CAN_BUFFER_SIZE = 100

# ── WebCam Configuration ──────────────────────────────────────────────────────

WEBCAM_INDEX  = 0     # OpenCV device index (0 = first camera)
FRAME_WIDTH   = 1280  # Capture resolution width  (pixels)
FRAME_HEIGHT  = 720   # Capture resolution height (pixels)
FRAME_FPS     = 30    # Target frames per second

# ── Data-Logging / dSpace Output Configuration ────────────────────────────────

LOG_DIR        = "logs"         # Directory where log files are stored
LOG_CAN_CSV    = True           # Write CAN messages to a CSV file
LOG_VIDEO      = True           # Write annotated video to a file
VIDEO_CODEC    = "mp4v"         # FourCC codec string for the output video
VIDEO_EXT      = ".mp4"         # Output video file extension

# ── Display / Overlay ─────────────────────────────────────────────────────────

SHOW_PREVIEW   = True           # Display live OpenCV preview window
OVERLAY_CAN    = True           # Overlay latest CAN values on the video frame
OVERLAY_FONT_SCALE  = 0.55
OVERLAY_THICKNESS   = 1

# Maximum number of CAN message rows shown in the overlay
OVERLAY_MAX_ROWS = 8
