"""
Main script for Media Dispenser control.
Runs homing (down until limit switch via PCF8574) and then up/down with fixed steps.

Media dispenser uses same pins as stepper.py: STEP=18, DIR=23, EN=24 (BCM).
"""
from media_dispenser import (
    Media_Disperensor_up,
    Media_Disperensor_down,
    media_dispensor_config,
    cleanup,
)
import RPi.GPIO as GPIO
import time
try:
    # First: move down until limit switch on P0 (PCF8574) is pressed
    media_dispensor_config()
    # Then run fixed-step movements
    Media_Disperensor_up(2600)   # 1000 steps up
    Media_Disperensor_down(800)
    for i in range(5):
        Media_Disperensor_down(520)
        time.sleep(5)   # 500 steps down
finally:
    cleanup()
    GPIO.cleanup()
