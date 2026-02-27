"""
Main script for Filteration Flask control.
Runs homing (down until limit switch via PCF8574) and then up/down with fixed steps.

Filteration flask uses same pins as stepper.py: STEP=18, DIR=23, EN=24 (BCM).
"""
from filteration_flask import (
    Filteration_flask_up,
    Filteration_flask_down,
    filteration_flask_config,
    cleanup,
)
import RPi.GPIO as GPIO
import time
try:
    # First: move down until limit switch on P0 (PCF8574) is pressed
    filteration_flask_config()
    # Then run fixed-step movements
    #Filteration_flask_up(1000)   # 1000 steps up
    #Filteration_flask_down(100)  # 500 steps down
    Filteration_flask_up(3500)   # 1000 steps up
    time.sleep(10)
    Filteration_flask_down(900)
    time.sleep(10)
    for i in range(5):
        Filteration_flask_down(520)
        time.sleep(5)   # 500 steps down
finally:
    cleanup()
    GPIO.cleanup()
