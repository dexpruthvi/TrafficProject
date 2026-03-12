# ============================================================
# DASHBOARD SERVER - Flask + SocketIO for real-time web dashboard
# ============================================================
#
# Serves the dashboard HTML and pushes live data via SocketIO.
# Run alongside main.py - dashboard auto-updates in real time.

import json
import os
import threading
from flask import Flask, send_from_directory, jsonify
from flask_socketio import SocketIO

from config import DASHBOARD_HOST, DASHBOARD_PORT, BASE_DIR

app = Flask(__name__, static_folder=os.path.join(BASE_DIR, "dashboard"))
app.config["SECRET_KEY"] = "traffic-ai-ryzen"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# Latest data (updated by main.py)
_latest_data = {}
_history_file = os.path.join(BASE_DIR, "dashboard", "history.json")


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


def update_dashboard(data):
    """Called by main.py to push new data to all connected clients."""
    global _latest_data
    _latest_data = data
    socketio.emit("traffic_update", data)


def start_server():
    """Start the Flask server in a background thread."""
    def run():
        print(f"[DASHBOARD] Starting at http://localhost:{DASHBOARD_PORT}")
        socketio.run(app, host=DASHBOARD_HOST, port=DASHBOARD_PORT,
                     allow_unsafe_werkzeug=True, log_output=False)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return thread
