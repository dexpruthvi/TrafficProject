# ============================================================
# SIREN DETECTOR - Detects emergency vehicle sirens via audio
# ============================================================
#
# Uses microphone input to detect siren frequency patterns.
# Sirens typically alternate between 500-1500 Hz.
# This gives DUAL CONFIRMATION: vision + audio = emergency vehicle.
#
# Falls back gracefully if no microphone is available.

import numpy as np
import threading
import time
from config import (
    SIREN_DETECTION_ENABLED, SIREN_SAMPLE_RATE, SIREN_DURATION,
    SIREN_MIN_FREQ, SIREN_MAX_FREQ, SIREN_ENERGY_THRESHOLD,
)


class SirenDetector:
    def __init__(self):
        self.enabled = SIREN_DETECTION_ENABLED
        self.siren_detected = False
        self.confidence = 0.0
        self._running = False
        self._thread = None
        self._sounddevice = None

        if not self.enabled:
            print("[SIREN] Siren detection disabled in config")
            return

        try:
            import sounddevice as sd
            self._sounddevice = sd
            print(f"[SIREN] Audio detection enabled (mic @ {SIREN_SAMPLE_RATE}Hz)")
        except (ImportError, OSError):
            self.enabled = False
            print("[SIREN] sounddevice not available - siren detection disabled")
            print("[SIREN] Install with: pip install sounddevice")

    def start(self):
        """Start background thread that continuously listens for sirens."""
        if not self.enabled:
            return
        self._running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        print("[SIREN] Listening for emergency sirens...")

    def stop(self):
        """Stop the listening thread."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)

    def _listen_loop(self):
        """Continuously record short audio clips and analyze them."""
        sd = self._sounddevice
        while self._running:
            try:
                # Record a short audio clip
                audio = sd.rec(
                    int(SIREN_DURATION * SIREN_SAMPLE_RATE),
                    samplerate=SIREN_SAMPLE_RATE,
                    channels=1,
                    dtype='float32',
                )
                sd.wait()

                # Analyze the audio
                self._analyze_audio(audio.flatten())

            except Exception:
                # Mic error - skip this cycle
                time.sleep(1)

    def _analyze_audio(self, audio):
        """
        Analyze audio for siren frequencies using FFT.
        Sirens have strong energy in 500-1500 Hz band with oscillating pattern.
        """
        if len(audio) == 0:
            self.siren_detected = False
            self.confidence = 0.0
            return

        # Compute FFT
        fft = np.fft.rfft(audio)
        magnitudes = np.abs(fft)
        freqs = np.fft.rfftfreq(len(audio), d=1.0 / SIREN_SAMPLE_RATE)

        # Total energy
        total_energy = np.sum(magnitudes ** 2)
        if total_energy == 0:
            self.siren_detected = False
            self.confidence = 0.0
            return

        # Energy in siren frequency band (500-1500 Hz)
        siren_mask = (freqs >= SIREN_MIN_FREQ) & (freqs <= SIREN_MAX_FREQ)
        siren_energy = np.sum(magnitudes[siren_mask] ** 2)

        # Ratio of siren-band energy to total
        siren_ratio = siren_energy / total_energy

        # Check for oscillation pattern (siren goes up-down)
        # Split siren band into low and high halves
        mid_freq = (SIREN_MIN_FREQ + SIREN_MAX_FREQ) / 2
        low_mask = (freqs >= SIREN_MIN_FREQ) & (freqs < mid_freq)
        high_mask = (freqs >= mid_freq) & (freqs <= SIREN_MAX_FREQ)
        low_energy = np.sum(magnitudes[low_mask] ** 2)
        high_energy = np.sum(magnitudes[high_mask] ** 2)

        # Both halves should have significant energy (oscillation)
        has_oscillation = low_energy > 0 and high_energy > 0
        if has_oscillation:
            balance = min(low_energy, high_energy) / max(low_energy, high_energy)
        else:
            balance = 0

        # Combined confidence
        self.confidence = min(1.0, siren_ratio * (1 + balance))
        self.siren_detected = (
            siren_ratio >= SIREN_ENERGY_THRESHOLD and balance > 0.1
        )

    def is_siren_detected(self):
        """Check if a siren is currently detected."""
        return self.siren_detected

    def get_confidence(self):
        """Get siren detection confidence (0.0 to 1.0)."""
        return round(self.confidence, 2)

    def get_status(self):
        """Get status dict for dashboard."""
        return {
            "enabled": bool(self.enabled),
            "siren_detected": bool(self.siren_detected),
            "confidence": float(self.get_confidence()),
        }
