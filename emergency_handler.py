# ============================================================
# EMERGENCY HANDLER - Green Corridor for ambulances/fire trucks
# ============================================================
#
# When an emergency vehicle is detected:
#   1. OVERRIDE all normal signal timings
#   2. Give GREEN to the lane where emergency vehicle is
#   3. Give RED to ALL other lanes
#   4. Hold this until emergency vehicle passes (or timeout)
#   5. Then return to normal adaptive mode

import time
from config import EMERGENCY_GREEN_TIME


class EmergencyHandler:
    def __init__(self):
        self.active = False
        self.corridor_lane = None
        self.activated_at = None

    def activate_corridor(self, lane_name):
        """
        Activate green corridor: one lane gets immediate GREEN, all others RED.
        """
        self.active = True
        self.corridor_lane = lane_name
        self.activated_at = time.time()
        print(f"\n{'='*50}")
        print(f"  EMERGENCY CORRIDOR ACTIVATED")
        print(f"  Lane: {lane_name} → GREEN")
        print(f"  All other lanes → RED")
        print(f"{'='*50}\n")
        return self.get_corridor_states()

    def get_corridor_states(self):
        """Get signal states during emergency corridor."""
        states = {}
        for lane in ["North", "South", "East", "West"]:
            if lane == self.corridor_lane:
                states[lane] = "GREEN"
            else:
                states[lane] = "RED"
        return states

    def check_timeout(self):
        """Check if corridor has been active long enough and should deactivate."""
        if self.active and self.activated_at:
            elapsed = time.time() - self.activated_at
            if elapsed >= EMERGENCY_GREEN_TIME:
                self.deactivate()
                return True
        return False

    def deactivate(self):
        """Turn off corridor, go back to normal adaptive mode."""
        print(f"\n{'='*50}")
        print(f"  EMERGENCY CORRIDOR DEACTIVATED")
        print(f"  Returning to adaptive mode...")
        print(f"{'='*50}\n")
        self.active = False
        self.corridor_lane = None
        self.activated_at = None

    def is_active(self):
        return self.active
