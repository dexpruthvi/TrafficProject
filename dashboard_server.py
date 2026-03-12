# ============================================================
# DASHBOARD SERVER - Flask + SocketIO for real-time web dashboard
# ============================================================
#
# Serves the dashboard HTML and pushes live data via SocketIO.
# Also serves MJPEG video stream of the annotated camera feed.
# Run alongside main.py - dashboard auto-updates in real time.

import json
import os
import threading
import time
import cv2
from flask import Flask, send_from_directory, jsonify, Response

from flask_socketio import SocketIO

from config import DASHBOARD_HOST, DASHBOARD_PORT, BASE_DIR

app = Flask(__name__, static_folder=os.path.join(BASE_DIR, "dashboard"))
app.config["SECRET_KEY"] = "traffic-ai-ryzen"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# Latest data (updated by main.py)
_latest_data = {}
_history_file = os.path.join(BASE_DIR, "dashboard", "history.json")

# Frame source for video streaming (set by main.py)
_get_frame = None
_frame_lock = None


def set_frame_source(getter, lock):
    """Called by main.py to provide access to the latest annotated frame."""
    global _get_frame, _frame_lock
    _get_frame = getter
    _frame_lock = lock


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/data.json")
def get_data():
    return jsonify(_latest_data)


@app.route("/history.json")
def get_history():
    try:
        with open(_history_file, "r") as f:
            return jsonify(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return jsonify([])


def _generate_mjpeg():
    """Generator that yields MJPEG frames for the video stream."""
    while True:
        frame = None
        if _get_frame and _frame_lock:
            with _frame_lock:
                frame = _get_frame()
        if frame is not None:
            ret, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            if ret:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' +
                       jpeg.tobytes() + b'\r\n')
        time.sleep(0.05)  # ~20 FPS


@app.route("/video_feed")
def video_feed():
    """MJPEG video stream endpoint for the live annotated camera feed."""
    return Response(_generate_mjpeg(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


def update_dashboard(data):
    """Called by main.py to push new data to all connected clients."""
    global _latest_data
    _latest_data = data
    socketio.emit("traffic_update", data)


def start_server():
    """Start the Flask server in a background thread."""
    def run():
        print(f"[DASHBOARD] Starting at http://localhost:{DASHBOARD_PORT}")
        print(f"[DASHBOARD] Live video at http://localhost:{DASHBOARD_PORT}/video_feed")
        socketio.run(app, host=DASHBOARD_HOST, port=DASHBOARD_PORT,
                     allow_unsafe_werkzeug=True, log_output=False)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return thread
