"""
Main script for Media Dispenser control.
Runs up then down with fixed steps.

Media dispenser uses same pins as stepper.py: STEP=18, DIR=23, EN=24 (BCM).
"""
from media_dispenser import Media_Disperensor_up, Media_Disperensor_down, cleanup
import RPi.GPIO as GPIO

try:
    Media_Disperensor_up(1000)   # 1000 steps up
    #Media_Disperensor_down(100)  # 500 steps down
finally:
    cleanup()
    GPIO.cleanup()
