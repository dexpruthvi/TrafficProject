# ============================================================
# SIGNAL OPTIMIZER - The brain: decides green time for each lane
# ============================================================
#
# CORE LOGIC:
#   More vehicles on a side  →  Longer green light
#   Fewer vehicles on a side →  Shorter green light
#
# Formula:
#   green_time = MIN_GREEN + (density_ratio) * (MAX_GREEN - MIN_GREEN)
#
# Example with 4 lanes:
#   North: 15 vehicles (50%)  → green = 10 + 0.50 * 50 = 35 seconds
#   South: 9 vehicles (30%)   → green = 10 + 0.30 * 50 = 25 seconds
#   East:  3 vehicles (10%)   → green = 10 + 0.10 * 50 = 15 seconds
#   West:  3 vehicles (10%)   → green = 10 + 0.10 * 50 = 15 seconds
#
# The busiest lane always gets the longest green.

from config import MIN_GREEN_TIME, MAX_GREEN_TIME, YELLOW_TIME


class SignalOptimizer:
    def __init__(self):
        self.current_green_lane = None
        self.lane_order = []

    def calculate_green_times(self, lane_counts, density):
        """
        Calculate how many seconds of green each lane should get.
        Busiest lane = longest green. Emptiest lane = shortest green.
        """
        timings = {}

        # Sort lanes by density: busiest first
        sorted_lanes = sorted(density.items(), key=lambda x: x[1], reverse=True)
        self.lane_order = [lane for lane, _ in sorted_lanes]

        green_range = MAX_GREEN_TIME - MIN_GREEN_TIME

        for lane, dens in sorted_lanes:
            # The formula: more density = more green time
            green = int(MIN_GREEN_TIME + dens * green_range)
            green = max(MIN_GREEN_TIME, min(MAX_GREEN_TIME, green))

            timings[lane] = {
                "green_time": green,
                "yellow_time": YELLOW_TIME,
                "vehicle_count": lane_counts[lane],
                "density_percent": round(dens * 100, 1),
            }

        return timings

    def get_signal_cycle(self, timings):
        """
        Generate the full traffic light cycle.
        Each lane gets green one at a time (busiest first), then yellow, then red.

        Returns a list like:
        [
            {"lane": "North", "state": "GREEN", "duration": 35},
            {"lane": "North", "state": "YELLOW", "duration": 3},
            {"lane": "South", "state": "GREEN", "duration": 25},
            {"lane": "South", "state": "YELLOW", "duration": 3},
            ...
        ]
        """
        cycle = []
        for lane in self.lane_order:
            cycle.append({
                "lane": lane,
                "state": "GREEN",
                "duration": timings[lane]["green_time"],
            })
            cycle.append({
                "lane": lane,
                "state": "YELLOW",
                "duration": timings[lane]["yellow_time"],
            })
        return cycle

    def get_all_lane_states(self, active_lane, state):
        """
        Given one lane that is GREEN (or YELLOW), set all others to RED.
        Returns: {"North": "GREEN", "South": "RED", "East": "RED", "West": "RED"}
        """
        states = {}
        for lane in self.lane_order:
            if lane == active_lane:
                states[lane] = state
            else:
                states[lane] = "RED"
        return states
