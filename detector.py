# VEHICLE DETECTOR - Uses YOLOv8 to detect objects in frame

from ultralytics import YOLO
import cv2
import numpy as np
from config import (
    MODEL_PATH, CONFIDENCE_THRESHOLD, VEHICLE_CLASSES,
    DISPLAY_CLASSES, CLASS_COLORS,
)


class VehicleDetector:
    def __init__(self):
        print("[DETECTOR] Loading YOLOv8 model...")
        self.model = YOLO(MODEL_PATH)
        print("[DETECTOR] Model loaded successfully")

    def detect(self, frame):
        """
        Detect all objects in a frame (persons, cars, trucks, bicycles, traffic lights).
        Returns:
          - vehicle_detections: list of vehicle-only detections (for traffic logic)
          - annotated_frame: frame with ALL detections drawn (like the demo image)
        """
        results = self.model(
            frame,
            conf=CONFIDENCE_THRESHOLD,
            classes=list(DISPLAY_CLASSES.keys()),
            verbose=False,
        )

        vehicle_detections = []
        annotated_frame = frame.copy()

        for box in results[0].boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            class_name = DISPLAY_CLASSES.get(cls_id, "unknown")

            # Draw bounding box and label for ALL detected objects
            color = CLASS_COLORS.get(class_name, (255, 255, 255))
            self._draw_box(annotated_frame, x1, y1, x2, y2, class_name, conf, color)

            # Only keep vehicles for traffic signal logic
            if cls_id in VEHICLE_CLASSES:
                vehicle_detections.append({
                    "bbox": (x1, y1, x2, y2),
                    "class_id": cls_id,
                    "class_name": VEHICLE_CLASSES[cls_id],
                    "confidence": conf,
                })

        return vehicle_detections, annotated_frame

    def _draw_box(self, frame, x1, y1, x2, y2, class_name, conf, color):
        """Draw a bounding box with a filled label background (like the demo image)."""
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

        label = f"{class_name} {int(conf * 100)}%"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        thickness = 1
        (tw, th), baseline = cv2.getTextSize(label, font, font_scale, thickness)

        # Filled rectangle behind the label text
        cv2.rectangle(frame, (x1, y1 - th - 8), (x1 + tw + 4, y1), color, -1)
        cv2.putText(frame, label, (x1 + 2, y1 - 4), font, font_scale,
                    (255, 255, 255), thickness, cv2.LINE_AA)

    def is_emergency_vehicle(self, frame, detection):
        """
        Check if a detected vehicle is an emergency vehicle (ambulance/fire truck)
        by analyzing the color of the vehicle region (red + white = likely emergency).
        """
        x1, y1, x2, y2 = detection["bbox"]
        roi = frame[y1:y2, x1:x2]
        if roi.size == 0:
            return False

        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        total_pixels = roi.shape[0] * roi.shape[1]

        # Detect RED (siren lights, fire truck body)
        mask_red1 = cv2.inRange(hsv, np.array([0, 120, 70]), np.array([10, 255, 255]))
        mask_red2 = cv2.inRange(hsv, np.array([170, 120, 70]), np.array([180, 255, 255]))
        red_pixels = cv2.countNonZero(mask_red1) + cv2.countNonZero(mask_red2)

        # Detect WHITE (ambulance body)
        mask_white = cv2.inRange(hsv, np.array([0, 0, 200]), np.array([180, 30, 255]))
        white_pixels = cv2.countNonZero(mask_white)

        red_ratio = red_pixels / total_pixels
        white_ratio = white_pixels / total_pixels

        # Significant red + white = likely emergency vehicle
        return red_ratio > 0.08 and white_ratio > 0.15
