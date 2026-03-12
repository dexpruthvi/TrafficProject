# ============================================================
# HISTORY LOGGER - Logs traffic data over time for analytics
# ============================================================
#
# Periodically saves traffic snapshots to a JSON file.
# The dashboard reads this to show historical charts:
#   - Vehicle count over time per lane
#   - Peak hour detection
#   - Average wait time trends

import json
import time
import os
from config import (
    HISTORY_ENABLED, HISTORY_LOG_INTERVAL,
    HISTORY_FILE, HISTORY_MAX_ENTRIES,
)


class HistoryLogger:
    def __init__(self):
        self.enabled = HISTORY_ENABLED
        self.last_log_time = 0
        self.entries = []
        self._load_existing()
        if self.enabled:
            print(f"[HISTORY] Logging to {HISTORY_FILE}")

    def _load_existing(self):
        """Load existing history file if it exists."""
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r") as f:
                    self.entries = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.entries = []

    def log(self, lane_counts, timings, lane_states, emergency_active, siren_status):
        """
        Log a traffic snapshot if enough time has passed.
        Called every frame, but only actually logs every HISTORY_LOG_INTERVAL seconds.
        """
        if not self.enabled:
            return

        now = time.time()
        if now - self.last_log_time < HISTORY_LOG_INTERVAL:
            return

        self.last_log_time = now

        entry = {
            "timestamp": now,
            "time_str": time.strftime("%H:%M:%S"),
            "total_vehicles": sum(lane_counts.values()),
            "emergency_active": emergency_active,
            "siren_detected": siren_status.get("siren_detected", False),
            "lanes": {},
        }

        for lane in lane_counts:
            entry["lanes"][lane] = {
                "vehicles": lane_counts[lane],
                "green_time": timings[lane]["green_time"] if lane in timings else 0,
                "density": timings[lane]["density_percent"] if lane in timings else 0,
                "state": lane_states.get(lane, "RED"),
            }

        self.entries.append(entry)

        # Keep only last N entries
        if len(self.entries) > HISTORY_MAX_ENTRIES:
            self.entries = self.entries[-HISTORY_MAX_ENTRIES:]

        self._save()

    def _save(self):
        """Write history to disk."""
        try:
            os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
            with open(HISTORY_FILE, "w") as f:
                json.dump(self.entries, f)
        except IOError:
            pass

    def get_stats(self):
        """Calculate summary statistics from history."""
        if not self.entries:
            return {
                "total_snapshots": 0,
                "avg_vehicles": 0,
                "peak_vehicles": 0,
                "peak_time": "N/A",
                "emergency_count": 0,
            }

        totals = [e["total_vehicles"] for e in self.entries]
        peak_idx = totals.index(max(totals))

        return {
            "total_snapshots": len(self.entries),
            "avg_vehicles": round(sum(totals) / len(totals), 1),
            "peak_vehicles": max(totals),
            "peak_time": self.entries[peak_idx]["time_str"],
            "emergency_count": sum(1 for e in self.entries if e["emergency_active"]),
        }
