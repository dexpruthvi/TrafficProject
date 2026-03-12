# VEHICLE DETECTOR - Uses YOLOv8 to detect vehicles in frame

from ultralytics import YOLO
import cv2
import numpy as np
from config import MODEL_PATH, CONFIDENCE_THRESHOLD, VEHICLE_CLASSES


class VehicleDetector:
    def __init__(self):
        print("[DETECTOR] Loading YOLOv8 model...")
        self.model = YOLO(MODEL_PATH)
        print("[DETECTOR] Model loaded successfully")

    def detect(self, frame):
        """
        Detect vehicles in a frame.
        Returns list of detections, each with bbox, class, confidence.
        Also returns the annotated frame (with boxes drawn).
        """
        results = self.model(
            frame,
            conf=CONFIDENCE_THRESHOLD,
            classes=list(VEHICLE_CLASSES.keys()),
            verbose=False,
        )

        detections = []
        for box in results[0].boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            detections.append({
                "bbox": (x1, y1, x2, y2),
                "class_id": cls_id,
                "class_name": VEHICLE_CLASSES.get(cls_id, "unknown"),
                "confidence": conf,
            })

        annotated_frame = results[0].plot()
        return detections, annotated_frame

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
