# Dynamic AI Traffic Flow Optimizer & Emergency Grid

> **Team Ryzen_4090Ti** | *India Innovates 2026*

A real-time adaptive traffic signal control system powered by **YOLOv8 computer vision** and **FFT-based audio analysis**. The system dynamically allocates green light time based on live traffic density, detects emergency vehicles through dual visual + audio confirmation, and activates priority green corridors — all viewable through a real-time web dashboard.

---

## Features

- **Adaptive Signal Control** — Dynamically adjusts green light duration per lane based on real-time vehicle density using YOLOv8 object detection.
- **Emergency Vehicle Detection (Dual Confirmation)** — Combines HSV color analysis (red + white patterns) with FFT-based siren audio detection (500–1500 Hz) for reliable emergency identification.
- **Emergency Corridor Activation** — Instantly grants green to the emergency lane and red to all others, with a 45-second auto-timeout.
- **Real-Time Web Dashboard** — Live 4-lane status, congestion heatmap, historical charts, emergency/siren banners, and session statistics via Flask + SocketIO.
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
   │   (Real)    │        │   (Fake Data)    │       │   (YOLOv8)      │
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
├── detector.py             # YOLOv8 vehicle detection + emergency color analysis
├── lane_manager.py         # Maps detections to lanes, calculates density
├── signal_optimizer.py     # Adaptive green time calculation algorithm
├── emergency_handler.py    # Emergency corridor activation and timeout
├── siren_detector.py       # Background audio FFT siren detection
├── arduino_comm.py         # Serial communication with Arduino
├── simulator.py            # Sine-wave traffic simulation for demos
├── dashboard_server.py     # Flask + SocketIO web server
├── history_logger.py       # Periodic traffic data logging
├── requirements.txt        # Python dependencies
├── dashboard/
│   ├── index.html          # Real-time web dashboard (Chart.js + SocketIO)
│   ├── data.json           # Latest traffic state
│   └── history.json        # Historical traffic snapshots
└── arduino_traffic/
    └── arduino_traffic.ino # Arduino sketch for physical LED control
```

---

## Prerequisites

- Python 3.8+
- pip

Install dependencies:

```bash
pip install -r requirements.txt
```

### Dependencies

| Package | Purpose |
|---------|---------|
| `ultralytics>=8.0.0` | YOLOv8 model and inference |
| `opencv-python>=4.8.0` | Camera input and image processing |
| `numpy>=1.24.0` | Array operations, FFT for audio |
| `pyserial>=3.5` | Serial communication with Arduino |
| `flask>=3.0.0` | Web dashboard server |
| `flask-socketio>=5.3.0` | Real-time SocketIO events |
| `sounddevice>=0.4.6` | Microphone input for siren detection |

---

## Quick Start

### Simulation Mode (default — no camera or hardware needed)

```bash
python main.py
```

Open the dashboard at **http://localhost:5050** to view real-time traffic visualization.

### Real Camera Mode

1. In `config.py`, set:
   ```python
   SIMULATION_MODE = False
   CAMERA_SOURCE = 0          # 0 for webcam, or path to a video file
   ```
2. Adjust `LANE_ROIS` coordinates to match your camera's field of view.
3. Run:
   ```bash
   python main.py
   ```
4. Press `q` to close the video window.

### With Arduino Hardware

1. Upload `arduino_traffic/arduino_traffic.ino` to your Arduino board.
2. Wire LEDs to pins 2–13 (3 per lane — see wiring section below).
3. In `config.py`, set:
   ```python
   ARDUINO_ENABLED = True
   ARDUINO_PORT = "/dev/cu.usbmodem*"  # macOS (Linux: /dev/ttyUSB0, Windows: COM3)
   ```
4. Run `python main.py`.

---

## Configuration

All settings are in `config.py`:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `SIMULATION_MODE` | `True` | Run with simulated traffic (no camera) |
| `MODEL_PATH` | `"yolov8n.pt"` | YOLOv8 model (auto-downloads on first run) |
| `CONFIDENCE_THRESHOLD` | `0.4` | Detection confidence cutoff |
| `MIN_GREEN_TIME` | `10s` | Minimum green light duration |
| `MAX_GREEN_TIME` | `60s` | Maximum green light duration |
| `YELLOW_TIME` | `3s` | Yellow light duration |
| `EMERGENCY_GREEN_TIME` | `45s` | Emergency corridor duration |
| `SIREN_DETECTION_ENABLED` | `True` | Enable audio siren detection |
| `ARDUINO_ENABLED` | `False` | Enable Arduino serial connection |
| `DASHBOARD_ENABLED` | `True` | Enable web dashboard |
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

On exit, the system displays session statistics including total vehicles detected, emergency events triggered, and peak traffic times.
