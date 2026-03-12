# ============================================================
# LANE MANAGER - Assigns vehicles to lanes and counts them
# ============================================================

from config import LANE_ROIS


class LaneManager:
    def __init__(self):
        self.lanes = LANE_ROIS

    def count_vehicles_per_lane(self, detections):
        """
        For each detection, check which lane ROI its center falls into.
        Returns:
            lane_counts: {"North": 5, "South": 2, "East": 8, "West": 1}
            lane_vehicles: {"North": [det1, det2, ...], ...}
        """
        lane_counts = {lane: 0 for lane in self.lanes}
        lane_vehicles = {lane: [] for lane in self.lanes}

        for det in detections:
            # Get center point of the vehicle bounding box
            x1, y1, x2, y2 = det["bbox"]
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2

            # Check which lane this center falls into
            for lane_name, (lx1, ly1, lx2, ly2) in self.lanes.items():
                if lx1 <= center_x <= lx2 and ly1 <= center_y <= ly2:
                    lane_counts[lane_name] += 1
                    lane_vehicles[lane_name].append(det)
                    break  # a vehicle belongs to only one lane

        return lane_counts, lane_vehicles

    def get_density_ratio(self, lane_counts):
        """
        Calculate what percentage of total traffic is in each lane.
        Example: North has 10 out of 20 total vehicles = 0.50 (50%)

        This ratio directly controls how long each lane gets green.
        """
        total = sum(lane_counts.values())
        if total == 0:
            # No vehicles anywhere - give equal time to all
            n = len(lane_counts)
            return {lane: 1.0 / n for lane in lane_counts}

        return {lane: count / total for lane, count in lane_counts.items()}
