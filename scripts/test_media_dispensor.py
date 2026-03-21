#!/usr/bin/env python3
"""Quick test for media dispensor stepper (BCM STEP=24, DIR=27). Run on the Raspberry Pi."""
import sys
import os

# Allow importing from repo root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import RPi.GPIO as GPIO
from Media_dispensor import Media_dispensor_up, Media_dispensor_down, cleanup

if __name__ == "__main__":
    try:
        print("Media dispensor test: 100 steps UP, then 100 DOWN (Ctrl+C to stop).")
        Media_dispensor_up(100)
        Media_dispensor_down(100)
        print("OK — if the motor moved both ways, wiring matches code.")
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        cleanup()
        try:
            GPIO.cleanup()
        except Exception:
            pass
