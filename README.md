# Dynamic AI Traffic Flow Optimizer & Emergency Grid

> **Team Ryzen_4090Ti** | *India Innovates 2026*

A real-time adaptive traffic signal control system powered by **YOLOv8 Nano computer vision** and **FFT-based audio analysis**. The system dynamically allocates green light time based on live traffic density, detects emergency vehicles through dual visual + audio confirmation, and activates priority green corridors — all viewable through a real-time web dashboard.

---

## Features

- **Adaptive Signal Control** — Dynamically adjusts green light duration per lane based on real-time vehicle density using YOLOv8n object detection across cars, motorcycles, buses, and trucks.
- **Multi-Class Detection & Display** — Detects and displays 7 object classes on screen: person, bicycle, car, motorcycle, bus, truck, and traffic light — each with a unique color overlay.
- **Emergency Vehicle Detection (Dual Confirmation)** — Combines HSV color analysis (red + white patterns) with FFT-based siren audio detection (500–1500 Hz) for reliable emergency identification.
- **Emergency Corridor Activation** — Instantly grants green to the emergency lane and red to all others, with a 45-second auto-timeout.
- **Real-Time Web Dashboard** — Live 4-lane status, congestion heatmap, historical charts, emergency/siren banners, and session statistics via Flask + SocketIO.
- **Live Camera Feed** — YOLOv8 annotated video stream served at `/video_feed` for remote monitoring.
- **Arduino Hardware Integration** — Controls physical traffic light LEDs over serial, with graceful fallback to simulation mode.
- **Traffic Simulation Mode** — Sine-wave-based realistic fake traffic generation for demos and testing without a camera.
- **Historical Data Logging** — Periodic JSON logging with peak hour detection and emergency event tracking.

---

## Architecture

```
                      ┌──────────────────────────────┐
                      │     main.py (Orchestrator)   │
                      └──────────────┬───────────────┘
                                     │
          ┌──────────────────────────┼──────────────────────────┐
          │                          │                          │
   ┌──────▼──────┐        ┌─────────▼────────┐       ┌────────▼────────┐
   │   Camera    │        │   simulator.py   │       │   detector.py   │
   │   (Real)    │        │   (Fake Data)    │       │   (YOLOv8n)     │
   └─────────────┘        └──────────────────┘       └─────────────────┘
                                     │
                          ┌──────────▼──────────┐
                          │   lane_manager.py   │
                          │  (Count & Density)  │
                          └──────────┬──────────┘
                                     │
          ┌──────────────────────────┼──────────────────────────┐
          │                          │                          │
  ┌───────▼──────────┐    ┌─────────▼──────────┐    ┌──────────▼──────────┐
  │ signal_optimizer  │    │ emergency_handler  │    │   siren_detector    │
  │ (Adaptive Timing) │    │ (Green Corridor)   │    │   (Audio FFT)       │
  └───────┬──────────┘    └─────────┬──────────┘    └──────────┬──────────┘
          └──────────────────────────┼──────────────────────────┘
                                     │
                          ┌──────────▼──────────┐
                          │   arduino_comm.py   │
                          │  (Serial Control)   │
                          └──────────┬──────────┘
                                     │
                          ┌──────────▼──────────┐
                          │   Arduino LEDs      │
                          │   (Physical)        │
                          └─────────────────────┘

  Running in parallel:
  ┌──────────────────────┐       ┌──────────────────────┐
  │  dashboard_server.py │       │   history_logger.py  │
  │  (Flask + SocketIO)  │       │   (JSON Logging)     │
  └──────────────────────┘       └──────────────────────┘
```

---

## Project Structure

```
TrafficProject/
├── main.py                 # Entry point — core orchestrator and main loop
├── config.py               # All configuration parameters
├── detector.py             # YOLOv8n vehicle detection + emergency color analysis
├── lane_manager.py         # Maps detections to lanes, calculates density
├── signal_optimizer.py     # Adaptive green time calculation algorithm
├── emergency_handler.py    # Emergency corridor activation and timeout
├── siren_detector.py       # Background audio FFT siren detection (22050 Hz)
├── arduino_comm.py         # Serial communication with Arduino (9600 baud)
├── simulator.py            # Sine-wave traffic simulation for demos
├── dashboard_server.py     # Flask + SocketIO web server (port 5050)
├── history_logger.py       # Periodic traffic data logging
├── yolov8n.pt              # YOLOv8 Nano pre-trained model weights
├── requirements.txt        # Python dependencies
├── dashboard/
│   ├── index.html          # Real-time web dashboard (Chart.js + SocketIO)
│   ├── data.json           # Latest traffic state (auto-generated)
│   └── history.json        # Historical traffic snapshots (auto-generated)
└── arduino_traffic/
    └── arduino_traffic.ino # Arduino sketch for physical LED control
```

---

## Prerequisites

- Python 3.8+
- pip
- Webcam (for real camera mode) or use simulation mode for demos
- Microphone (for siren detection — optional)
- Arduino board (for physical LED control — optional)

Install dependencies:

```bash
pip install -r requirements.txt
```

### Dependencies

| Package | Purpose |
|---------|---------|
| `ultralytics>=8.0.0` | YOLOv8 model loading and inference |
| `opencv-python>=4.8.0` | Camera capture, frame processing, and annotation |
| `numpy>=1.24.0` | Array operations, FFT for siren audio analysis |
| `pyserial>=3.5` | Serial communication with Arduino |
| `flask>=3.0.0` | Web dashboard server |
| `flask-socketio>=5.3.0` | Real-time SocketIO events for live dashboard |
| `sounddevice>=0.4.6` | Microphone input for siren detection |

---

## Quick Start

### Real Camera Mode (default)

By default, the system uses your webcam (`CAMERA_SOURCE = 0`) with real YOLOv8 detection:

```bash
python main.py
```

- A video window opens showing live detections with bounding boxes.
- The dashboard is available at **http://localhost:5050**.
- The live annotated video feed is at **http://localhost:5050/video_feed**.
- Press `q` in the video window or `Ctrl+C` in terminal to quit.

### Simulation Mode (no camera needed)

1. In `config.py`, set:
   ```python
   SIMULATION_MODE = True
   ```
2. Run:
   ```bash
   python main.py
   ```
3. Open **http://localhost:5050** to view the dashboard with simulated traffic data.

### Using a Video File

1. In `config.py`, set:
   ```python
   SIMULATION_MODE = False
   CAMERA_SOURCE = "path/to/traffic_video.mp4"
   ```
2. Run `python main.py`.

### With Arduino Hardware

1. Upload `arduino_traffic/arduino_traffic.ino` to your Arduino board.
2. Wire LEDs to pins 2–13 (3 per lane — see wiring section below).
3. In `config.py`, set:
   ```python
   ARDUINO_ENABLED = True
   ARDUINO_PORT = "/dev/cu.usbmodem*"  # macOS
   # ARDUINO_PORT = "/dev/ttyUSB0"     # Linux
   # ARDUINO_PORT = "COM3"             # Windows
   ```
4. Run `python main.py`.

---

## Configuration

All settings are in `config.py`:

### Detection

| Parameter | Default | Description |
|-----------|---------|-------------|
| `MODEL_PATH` | `"yolov8n.pt"` | YOLOv8 Nano model (auto-downloads on first run) |
| `CONFIDENCE_THRESHOLD` | `0.3` | Detection confidence cutoff |
| `VEHICLE_CLASSES` | cars, motorcycles, buses, trucks | COCO class IDs used for traffic signal logic |
| `DISPLAY_CLASSES` | 7 classes | All classes displayed on screen with bounding boxes |

### Signal Timing

| Parameter | Default | Description |
|-----------|---------|-------------|
| `MIN_GREEN_TIME` | `10s` | Minimum green light duration |
| `MAX_GREEN_TIME` | `60s` | Maximum green light duration |
| `YELLOW_TIME` | `3s` | Yellow light duration |
| `DEFAULT_GREEN_TIME` | `30s` | Green time when no vehicles detected |

### Camera & Lanes

| Parameter | Default | Description |
|-----------|---------|-------------|
| `CAMERA_SOURCE` | `0` | Webcam index or path to video file |
| `FRAME_WIDTH` | `1280` | Input frame resize width |
| `FRAME_HEIGHT` | `720` | Input frame resize height |
| `LANE_ROIS` | 4 quadrants | Region of interest per lane (x1, y1, x2, y2) |

### Emergency & Siren

| Parameter | Default | Description |
|-----------|---------|-------------|
| `EMERGENCY_ENABLED` | `True` | Enable visual emergency vehicle detection |
| `EMERGENCY_GREEN_TIME` | `45s` | Emergency corridor duration |
| `SIREN_DETECTION_ENABLED` | `True` | Enable audio siren detection via microphone |
| `SIREN_SAMPLE_RATE` | `22050` | Audio sample rate (Hz) |
| `SIREN_DURATION` | `2s` | Audio window per FFT analysis |
| `SIREN_MIN_FREQ` / `SIREN_MAX_FREQ` | `500–1500 Hz` | Siren frequency band |
| `SIREN_ENERGY_THRESHOLD` | `0.3` | Minimum energy ratio in siren band to trigger |

### Hardware & Services

| Parameter | Default | Description |
|-----------|---------|-------------|
| `SIMULATION_MODE` | `False` | Run with simulated traffic (no camera) |
| `ARDUINO_ENABLED` | `False` | Enable Arduino serial connection |
| `ARDUINO_PORT` | `"/dev/ttyUSB0"` | Serial port for Arduino |
| `ARDUINO_BAUD` | `9600` | Serial baud rate |
| `DASHBOARD_ENABLED` | `True` | Enable web dashboard |
| `DASHBOARD_HOST` | `"0.0.0.0"` | Dashboard bind address |
| `DASHBOARD_PORT` | `5050` | Dashboard server port |
| `HISTORY_LOG_INTERVAL` | `5s` | Seconds between log entries |
| `HISTORY_MAX_ENTRIES` | `500` | Max historical snapshots kept |

---

## Signal Optimization Algorithm

Green time is allocated proportionally to traffic density:

```
green_time = MIN_GREEN + density_ratio × (MAX_GREEN - MIN_GREEN)
```

**Example:**

| Lane | Vehicles | Density | Green Time |
|------|----------|---------|------------|
| North | 15 | 50% | 35s |
| South | 9 | 30% | 25s |
| East | 3 | 10% | 15s |
| West | 3 | 10% | 15s |

Lanes are served in order of density — busiest lane gets green first.

---

## Arduino Wiring

| Lane | RED Pin | YELLOW Pin | GREEN Pin |
|------|---------|------------|-----------|
| North | 2 | 3 | 4 |
| South | 5 | 6 | 7 |
| East | 8 | 9 | 10 |
| West | 11 | 12 | 13 |

**Serial Protocol:** `N:G,S:R,E:R,W:R\n`
- Lane codes: `N` / `S` / `E` / `W`
- State codes: `G` (Green) / `R` (Red) / `Y` (Yellow)

---

## Dashboard

The web dashboard at `http://localhost:5050` provides:

- **Live signal states** — Color-coded lane cards with vehicle counts, green times, and density
- **Live camera feed** — YOLOv8 annotated video stream at `/video_feed`
- **Congestion heatmap** — 2×2 grid with color coding from green (empty) to red (congested)
- **Historical chart** — Line chart tracking vehicle counts per lane over time
- **Emergency alerts** — Red banner when emergency corridor is active
- **Siren detection** — Orange banner with confidence percentage
- **Session statistics** — Total vehicles, busiest lane, average wait time, emergency count

Updates via SocketIO (real-time push) with polling fallback every 800ms.

---

## Controls

| Key | Action |
|-----|--------|
| `q` | Close video window (camera mode) |
| `Ctrl+C` | Quit the application |

On exit, the system displays session statistics including total snapshots processed, average/peak vehicle counts, and emergency events triggered.
