# CONFIGURATION - Dynamic AI Traffic Flow Optimizer


import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ---- YOLO Model ----
MODEL_PATH = "yolov8n.pt"  # auto-downloads on first run
CONFIDENCE_THRESHOLD = 0.3

# COCO class IDs for vehicles (used for traffic signal logic)
VEHICLE_CLASSES = {2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}

# ALL classes to detect and display on screen (like the demo image)
DISPLAY_CLASSES = {
    0: "person", 1: "bicycle", 2: "car", 3: "motorcycle",
    5: "bus", 7: "truck", 9: "traffic light",
}

# Colors (BGR) for each display class - matches the demo image style
CLASS_COLORS = {
    "person":        (0, 0, 255),       # red
    "bicycle":       (0, 255, 0),       # green
    "car":           (255, 0, 0),       # blue
    "motorcycle":    (255, 0, 255),     # magenta
    "bus":           (0, 165, 255),     # orange
    "truck":         (0, 200, 0),       # green
    "traffic light": (255, 0, 255),     # magenta
}

# ---- Signal Timing (seconds) ----
MIN_GREEN_TIME = 10   # minimum green even if lane is empty
MAX_GREEN_TIME = 60   # maximum green even if lane is packed
YELLOW_TIME = 3
DEFAULT_GREEN_TIME = 30  # used when no vehicles detected

# ---- Camera Source ----
# Use 0 for webcam, or path to video file for demo
# Example: CAMERA_SOURCE = "demo_traffic.mp4"
CAMERA_SOURCE = 0

# ---- Frame Resolution (resize input for consistent lane ROIs) ----
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720

# ---- Lane ROIs (Region of Interest) ----
# These define rectangular zones on the camera frame for each lane
# Format: (x1, y1, x2, y2) - top-left and bottom-right corners
# IMPORTANT: Adjust these values based on your actual camera angle
LANE_ROIS = {
    "North": (0, 0, 640, 360),
    "South": (640, 0, 1280, 360),
    "East":  (0, 360, 640, 720),
    "West":  (640, 360, 1280, 720),
}

# ---- Emergency Vehicle Detection ----
EMERGENCY_ENABLED = True
EMERGENCY_GREEN_TIME = 45  # how long corridor stays open (seconds)

# ---- Siren Audio Detection ----
SIREN_DETECTION_ENABLED = True
SIREN_SAMPLE_RATE = 22050
SIREN_DURATION = 2        # seconds of audio to analyze per check
SIREN_MIN_FREQ = 500      # Hz - siren low frequency
SIREN_MAX_FREQ = 1500     # Hz - siren high frequency
SIREN_ENERGY_THRESHOLD = 0.3  # how much energy must be in siren band

# ---- Arduino ----
ARDUINO_ENABLED = False  # set True when Arduino is connected
ARDUINO_PORT = "/dev/ttyUSB0"  # Linux: /dev/ttyUSB0, Mac: /dev/cu.usbmodem*, Windows: COM3
ARDUINO_BAUD = 9600

# ---- Dashboard (Flask server) ----
DASHBOARD_ENABLED = True
DASHBOARD_HOST = "0.0.0.0"
DASHBOARD_PORT = 5050

# ---- Historical Data Logging ----
HISTORY_ENABLED = True
HISTORY_LOG_INTERVAL = 5   # log data every N seconds
HISTORY_FILE = os.path.join(BASE_DIR, "dashboard", "history.json")
HISTORY_MAX_ENTRIES = 500  # keep last N entries to avoid huge files

# ---- Simulation Mode ----
# When True, generates fake traffic data so you can demo without a camera
SIMULATION_MODE = False
