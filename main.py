"""
Main script for Filteration Flask and Suction Pump control.
Runs homing (down until limit switch via PCF8574) and then movements.

Filteration flask uses same pins as stepper.py: STEP=18, DIR=23, EN=24 (BCM).
Suction pump uses separate GPIO pins (see suction_pump.py).
"""
from filteration_flask import (
    Filteration_flask_up,
    Filteration_flask_down,
    filteration_flask_config,
    cleanup as filteration_cleanup,
)
from suction_pump import (
    Suction_pump_up,
    Suction_pump_down,
    suction_pump_config,
    cleanup as suction_cleanup,
)
import RPi.GPIO as GPIO
import time

try:
    # Filteration flask: move down until limit switch on P0 (PCF8574) is pressed
    #filteration_flask_config()
    #Filteration_flask_up(1150)

    # Suction pump: move down until limit switch on P1 (PCF8574) is pressed
    suction_pump_config()
    Suction_pump_up(1000)
finally:
    # Clean up both modules
    filteration_cleanup()
    suction_cleanup()
    GPIO.cleanup()
