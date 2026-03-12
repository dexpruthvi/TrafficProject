# ============================================================
# MAIN.PY - Dynamic AI Traffic Flow Optimizer & Emergency Grid
# ============================================================
#
# This is the main program that ties everything together:
#
#   Camera → Detect Vehicles → Count Per Lane → Calculate Density
#     → Decide Green Times → Control Signals
#
#   If ambulance detected (vision + siren audio) → Green Corridor
#
#   Simulation mode available for demo without camera.
#
# Run:   python main.py
# Quit:  Press 'q' in the video window (or Ctrl+C in terminal)

import cv2
import time
import json
import os
import threading

from config import (
    CAMERA_SOURCE, LANE_ROIS, EMERGENCY_ENABLED,
    DASHBOARD_ENABLED, SIMULATION_MODE,
    SIREN_DETECTION_ENABLED,
    FRAME_WIDTH, FRAME_HEIGHT, BASE_DIR,
)

from lane_manager import LaneManager
from signal_optimizer import SignalOptimizer
from emergency_handler import EmergencyHandler
from arduino_comm import ArduinoController
from siren_detector import SirenDetector
from history_logger import HistoryLogger

# Global: latest annotated frame for dashboard video stream
latest_frame = None
frame_lock = threading.Lock()


# ── Terminal colors ─────────────────────────────────────────
class Color:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    END = "\033[0m"


# ── Drawing helpers (for camera mode) ──────────────────────
def draw_lane_rois(frame):
    colors = {
        "North": (0, 255, 0),
        "South": (0, 0, 255),
        "East":  (255, 0, 0),
        "West":  (0, 255, 255),
    }
    for lane_name, (x1, y1, x2, y2) in LANE_ROIS.items():
        color = colors.get(lane_name, (255, 255, 255))
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(frame, lane_name, (x1 + 5, y1 + 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    return frame


def draw_signal_info(frame, timings, lane_order, lane_states, emergency_active, siren_status):
    # Semi-transparent overlay panel at top-left
    overlay = frame.copy()
    panel_h = len(lane_order) * 30 + 20
    cv2.rectangle(overlay, (5, 5), (480, panel_h), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

    y = 30
    for lane in lane_order:
        info = timings[lane]
        state = lane_states.get(lane, "RED")
        if state == "GREEN":
            color = (0, 255, 0)
        elif state == "YELLOW":
            color = (0, 255, 255)
        else:
            color = (0, 0, 255)

        # Draw signal circle
        cv2.circle(frame, (22, y - 5), 8, color, -1)

        wait = info.get("estimated_wait", 0)
        text = (f"{lane}: {info['vehicle_count']} veh | "
                f"G:{info['green_time']}s | "
                f"D:{info['density_percent']}% | "
                f"Wait:{wait}s")
        cv2.putText(frame, text, (38, y), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
        y += 30

    if emergency_active:
        cv2.putText(frame, "** EMERGENCY CORRIDOR ACTIVE **",
                    (10, frame.shape[0] - 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2, cv2.LINE_AA)

    if siren_status.get("siren_detected"):
        cv2.putText(frame, f"SIREN ({int(siren_status['confidence']*100)}%)",
                    (10, frame.shape[0] - 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2, cv2.LINE_AA)
    return frame


# ── Terminal status printer ────────────────────────────────
def print_status(lane_counts, timings, lane_order, lane_states, emergency_active, siren_status):
    print(f"\n{Color.CYAN}{'─'*68}{Color.END}")
    if emergency_active:
        print(f"{Color.RED}{Color.BOLD}  *** EMERGENCY CORRIDOR ACTIVE ***{Color.END}")
    else:
        print(f"{Color.BOLD}  ADAPTIVE TRAFFIC SIGNAL STATUS{Color.END}")
    if siren_status.get("siren_detected"):
        print(f"{Color.RED}  SIREN DETECTED (confidence: {int(siren_status['confidence']*100)}%){Color.END}")
    print(f"{Color.CYAN}{'─'*68}{Color.END}")

    for lane in lane_order:
        count = lane_counts.get(lane, 0)
        info = timings.get(lane, {})
        state = lane_states.get(lane, "RED")
        wait = info.get("estimated_wait", 0)

        if state == "GREEN":
            s = f"{Color.GREEN}GREEN {Color.END}"
        elif state == "YELLOW":
            s = f"{Color.YELLOW}YELLOW{Color.END}"
        else:
            s = f"{Color.RED}RED   {Color.END}"

        bar = "█" * min(count, 25) + "░" * (25 - min(count, 25))
        print(f"  {lane:6s} │ {s} │ {count:3d} veh │ "
              f"G:{info.get('green_time',0):2d}s │ Wait:{wait:3d}s │ {bar}")
    print(f"{Color.CYAN}{'─'*68}{Color.END}")


# ── Dashboard data helpers ─────────────────────────────────
def build_dashboard_data(lane_counts, timings, lane_states, emergency_active, siren_status):
    data = {
        "timestamp": time.time(),
        "time_str": time.strftime("%H:%M:%S"),
        "emergency_active": emergency_active,
        "siren": siren_status,
        "lanes": {},
    }
    for lane in lane_counts:
        t = timings.get(lane, {})
        data["lanes"][lane] = {
            "vehicle_count": lane_counts[lane],
            "green_time": t.get("green_time", 10),
            "density_percent": t.get("density_percent", 0),
            "signal_state": lane_states.get(lane, "RED"),
            "estimated_wait": t.get("estimated_wait", 0),
        }
    return data


def save_dashboard_json(data):
    path = os.path.join(BASE_DIR, "dashboard", "data.json")
    try:
        with open(path, "w") as f:
            json.dump(data, f)
    except IOError:
        pass


# ============================================================
#  MAIN LOOP
# ============================================================
def main():
    print(f"\n{Color.BOLD}{'='*68}")
    print("  Dynamic AI Traffic Flow Optimizer & Emergency Grid")
    print("  Team Ryzen_4090Ti | India Innovates 2026")
    print(f"{'='*68}{Color.END}\n")

    # ── Init modules ────────────────────────────────────────
    lane_mgr = LaneManager()
    optimizer = SignalOptimizer()
    emergency = EmergencyHandler()
    arduino = ArduinoController()
    siren = SirenDetector()
    history = HistoryLogger()

    # Dashboard server (runs in background thread)
    _update_dashboard = None
    if DASHBOARD_ENABLED:
        try:
            from dashboard_server import start_server, update_dashboard, set_frame_source
            set_frame_source(lambda: latest_frame, frame_lock)
            start_server()
            _update_dashboard = update_dashboard
        except Exception as e:
            print(f"[DASHBOARD] Server failed: {e}")

    # Start siren audio detection
    siren.start()

    # ── Camera or Simulation mode ───────────────────────────
    cap = None
    sim = None
    detector = None

    if SIMULATION_MODE:
        from simulator import TrafficSimulator
        sim = TrafficSimulator()
    else:
        from detector import VehicleDetector
        detector = VehicleDetector()
        print(f"[CAMERA] Opening: {CAMERA_SOURCE}")
        cap = cv2.VideoCapture(CAMERA_SOURCE, cv2.CAP_AVFOUNDATION)
        if not cap.isOpened():
            print("[ERROR] Cannot open camera/video!")
            print("  Tip: Set SIMULATION_MODE = True in config.py to demo without a camera")
            return
        print(f"[CAMERA] Resolution: {int(cap.get(3))}x{int(cap.get(4))}")

    print(f"\n[SYSTEM] Running... Press 'q' to quit.\n")

    # ── State ───────────────────────────────────────────────
    default_timing = {"green_time": 10, "density_percent": 25.0,
                      "vehicle_count": 0, "estimated_wait": 0}
    current_lane_states = {lane: "RED" for lane in LANE_ROIS}
    current_timings = {lane: dict(default_timing) for lane in LANE_ROIS}
    current_lane_order = list(LANE_ROIS.keys())
    current_lane_counts = {lane: 0 for lane in LANE_ROIS}

    last_update = 0
    last_print = 0
    update_interval = 2
    print_interval = 3

    cycle_index = 0
    phase_start_time = 0
    signal_cycle = []

    try:
        while True:
            now = time.time()
            siren_status = siren.get_status()

            # ── Get detections ──────────────────────────────
            if SIMULATION_MODE:
                lane_counts = sim.get_simulated_counts()
                detections = sim.generate_fake_detections(lane_counts)
                annotated = None

                should_emergency, emer_lane = sim.should_trigger_emergency()
            else:
                ret, frame = cap.read()
                if not ret:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
                detections, annotated = detector.detect(frame)

                # Store annotated frame for dashboard live stream
                with frame_lock:
                    latest_frame = annotated.copy()

                should_emergency = False
                emer_lane = None

                # Visual emergency detection
                if EMERGENCY_ENABLED and not emergency.is_active():
                    for det in detections:
                        if detector.is_emergency_vehicle(frame, det):
                            cnt, vehs = lane_mgr.count_vehicles_per_lane([det])
                            for ln, v in vehs.items():
                                if v:
                                    should_emergency = True
                                    emer_lane = ln
                                    break
                            if should_emergency:
                                break

            # ── Siren audio can also trigger emergency ──────
            if (SIREN_DETECTION_ENABLED and siren.is_siren_detected()
                    and not emergency.is_active() and not should_emergency):
                if SIMULATION_MODE:
                    lc = lane_counts
                else:
                    lc, _ = lane_mgr.count_vehicles_per_lane(detections)
                emer_lane = max(lc, key=lc.get)
                should_emergency = True

            # ── Activate corridor ───────────────────────────
            if should_emergency and not emergency.is_active():
                corridor_states = emergency.activate_corridor(emer_lane)
                current_lane_states = corridor_states
                arduino.send_signals(corridor_states)

            # ── Handle active corridor ──────────────────────
            if emergency.is_active():
                emergency.check_timeout()
                if emergency.is_active():
                    current_lane_states = emergency.get_corridor_states()

            # ── Normal adaptive mode ────────────────────────
            if not emergency.is_active():
                if not SIMULATION_MODE:
                    lane_counts, _ = lane_mgr.count_vehicles_per_lane(detections)

                density = lane_mgr.get_density_ratio(lane_counts)
                current_lane_counts = lane_counts

                if now - last_update >= update_interval:
                    timings = optimizer.calculate_green_times(lane_counts, density)

                    # Calculate estimated wait time per lane
                    cycle = optimizer.get_signal_cycle(timings)
                    wait_acc = 0
                    for phase in cycle:
                        if phase["state"] == "GREEN":
                            timings[phase["lane"]]["estimated_wait"] = wait_acc
                            wait_acc += phase["duration"]

                    current_timings = timings
                    current_lane_order = optimizer.lane_order
                    signal_cycle = cycle
                    cycle_index = 0
                    phase_start_time = now
                    last_update = now

                if signal_cycle:
                    cur_phase = signal_cycle[cycle_index]
                    elapsed = now - phase_start_time
                    current_lane_states = optimizer.get_all_lane_states(
                        cur_phase["lane"], cur_phase["state"]
                    )
                    arduino.send_signals(current_lane_states)
                    if elapsed >= cur_phase["duration"]:
                        cycle_index = (cycle_index + 1) % len(signal_cycle)
                        phase_start_time = now

            # ── Dashboard + History ─────────────────────────
            dash_data = build_dashboard_data(
                current_lane_counts, current_timings,
                current_lane_states, emergency.is_active(), siren_status,
            )
            save_dashboard_json(dash_data)
            if _update_dashboard:
                _update_dashboard(dash_data)

            history.log(current_lane_counts, current_timings,
                        current_lane_states, emergency.is_active(), siren_status)

            # ── Display ─────────────────────────────────────
            if not SIMULATION_MODE and annotated is not None:
                annotated = draw_lane_rois(annotated)
                annotated = draw_signal_info(
                    annotated, current_timings, current_lane_order,
                    current_lane_states, emergency.is_active(), siren_status,
                )
                # Update the frame for dashboard live stream (with overlays)
                with frame_lock:
                    latest_frame = annotated.copy()

                cv2.imshow("Traffic AI - Ryzen_4090Ti", annotated)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            else:
                if now - last_print >= print_interval:
                    print_status(current_lane_counts, current_timings,
                                 current_lane_order, current_lane_states,
                                 emergency.is_active(), siren_status)
                    last_print = now
                time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n[SYSTEM] Interrupted")

    # ── Cleanup ─────────────────────────────────────────────
    siren.stop()
    if cap:
        cap.release()
    cv2.destroyAllWindows()
    arduino.close()

    stats = history.get_stats()
    print(f"\n{Color.BOLD}Session Stats:{Color.END}")
    print(f"  Snapshots:          {stats['total_snapshots']}")
    print(f"  Avg vehicles:       {stats['avg_vehicles']}")
    print(f"  Peak:               {stats['peak_vehicles']} at {stats['peak_time']}")
    print(f"  Emergency events:   {stats['emergency_count']}")
    print(f"\n[SYSTEM] Shutdown complete.\n")


if __name__ == "__main__":
    main()
