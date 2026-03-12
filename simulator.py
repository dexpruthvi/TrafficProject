# ============================================================
# TRAFFIC SIMULATOR - Generates fake traffic for demo mode
# ============================================================
#
# When you don't have a real camera, this generates realistic
# fake vehicle counts that change over time, so you can demo
# the full system (dashboard, signals, emergency corridor).

import random
import time
import math


class TrafficSimulator:
    def __init__(self):
        self.start_time = time.time()
        self.emergency_triggered = False
        self.emergency_cooldown = 0
        print("[SIMULATOR] Running in simulation mode (no camera needed)")

    def get_simulated_counts(self):
        """
        Generate realistic-looking vehicle counts that change over time.
        Uses sine waves to simulate traffic flow patterns.
        """
        t = time.time() - self.start_time

        # Each lane has a different traffic pattern (offset sine waves)
        counts = {
            "North": self._wave_count(t, offset=0, base=8, amplitude=12),
            "South": self._wave_count(t, offset=2, base=5, amplitude=8),
            "East":  self._wave_count(t, offset=4, base=6, amplitude=10),
            "West":  self._wave_count(t, offset=6, base=4, amplitude=7),
        }

        return counts

    def _wave_count(self, t, offset, base, amplitude):
        """Generate a vehicle count using sine wave + noise."""
        # Slow sine wave (period ~30 seconds) + faster variation
        wave = math.sin((t + offset) / 15) * amplitude
        noise = random.randint(-2, 2)
        count = max(0, int(base + wave + noise))
        return count

    def should_trigger_emergency(self):
        """
        Randomly trigger an emergency vehicle every ~60 seconds.
        Returns (should_trigger, lane_name) tuple.
        """
        if self.emergency_cooldown > 0:
            self.emergency_cooldown -= 1
            return False, None

        # ~1% chance per call (called every 2 seconds = roughly every 200s on average)
        if random.random() < 0.015:
            lane = random.choice(["North", "South", "East", "West"])
            self.emergency_cooldown = 30  # cooldown: don't trigger again too soon
            return True, lane

        return False, None

    def generate_fake_detections(self, lane_counts):
        """
        Generate fake detection dicts (matching the format from detector.py).
        Used so the rest of the pipeline works identically.
        """
        from config import LANE_ROIS

        detections = []
        for lane_name, count in lane_counts.items():
            x1, y1, x2, y2 = LANE_ROIS[lane_name]
            for i in range(count):
                # Place fake vehicles spread across the lane
                cx = random.randint(x1 + 20, x2 - 20)
                cy = random.randint(y1 + 20, y2 - 20)
                w, h = random.randint(30, 60), random.randint(25, 50)

                vehicle_type = random.choices(
                    [2, 3, 5, 7],          # car, motorcycle, bus, truck
                    weights=[60, 20, 10, 10],
                )[0]

                detections.append({
                    "bbox": (cx - w//2, cy - h//2, cx + w//2, cy + h//2),
                    "class_id": vehicle_type,
                    "class_name": {2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}[vehicle_type],
                    "confidence": round(random.uniform(0.6, 0.95), 2),
                })

        return detections
