# ARDUINO CONTROLLER - Sends signal commands to Arduino via serial
#
# Protocol: sends a string like "N:G,S:R,E:R,W:R\n"
#   N = North, S = South, E = East, W = West
#   G = Green, R = Red, Y = Yellow
#
# If Arduino is not connected, runs in simulation mode (prints to console).

import serial
import time
from config import ARDUINO_ENABLED, ARDUINO_PORT, ARDUINO_BAUD


class ArduinoController:
    def __init__(self):
        self.connected = False
        if ARDUINO_ENABLED:
            try:
                self.serial = serial.Serial(ARDUINO_PORT, ARDUINO_BAUD, timeout=1)
                time.sleep(2)  # Arduino resets on serial connect
                self.connected = True
                print(f"[ARDUINO] Connected on {ARDUINO_PORT}")
            except Exception as e:
                print(f"[ARDUINO] Connection failed: {e}")
                print("[ARDUINO] Running in simulation mode")
        else:
            print("[ARDUINO] Disabled in config - running in simulation mode")

    def send_signals(self, lane_states):
        """
        Send signal states to Arduino.
        lane_states: {"North": "GREEN", "South": "RED", "East": "RED", "West": "RED"}
        """
        # Build message: "N:G,S:R,E:R,W:R"
        parts = []
        for lane, state in lane_states.items():
            parts.append(f"{lane[0]}:{state[0]}")
        message = ",".join(parts) + "\n"

        if self.connected:
            self.serial.write(message.encode())

        return message.strip()

    def close(self):
        if self.connected:
            self.serial.close()
            print("[ARDUINO] Connection closed")
