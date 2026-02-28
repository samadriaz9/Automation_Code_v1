"""
Main script for Filteration Flask, Filteration Unit and Suction Pump control.
Runs homing (down until limit switch via PCF8574) and then movements.

Filteration flask uses same pins as stepper.py: STEP=18, DIR=23, EN=24 (BCM).
Filteration unit uses CLK=13, CW=19, EN=26 (BCM).
Suction pump uses separate GPIO pins (see suction_pump.py).
"""
from suction_pump_up_down import (suction_pump_up,
 suction_pump_off, suction_pump_home,
 suction_pump_on, suction_pump_off)
from filteration_flask import (
    Filteration_flask_up,
    Filteration_flask_down,
    filteration_flask_config,
    cleanup as filteration_cleanup,
)
from filteration_unit import (
    Filteration_unit_up,
    Filteration_unit_down,
    filteration_unit_config,
    cleanup as filteration_unit_cleanup,
)
from suction_pump import (
    suction_pump,
    cleanup as suction_cleanup,
)
from consumable import (
    Consumable_up,
    Consumable_down,
    cleanup as consumable_cleanup,
)
from relay_control import (
    P0,
    P1,
    P2,
    P3,
    P4,
    P5,
    P6,
    P7,
    run_relay,
    run_relay_sequence,
    cleanup as relay_cleanup,
)
import RPi.GPIO as GPIO
import time

try:
    suction_pump_home()   # step 1
    suction_pump_up(230)  # step 2
    Consumable_up(300)    # step 3

    # ✅ start pump
    suction_pump_on(100)

    # ✅ move stepper while pump is running
    suction_pump_up(1150)

    # ✅ stop pump immediately after motion
    suction_pump_off()

finally:
    # Clean up all modules
    filteration_cleanup()
    filteration_unit_cleanup()
    suction_cleanup()
    consumable_cleanup()
    relay_cleanup()
    GPIO.cleanup()
