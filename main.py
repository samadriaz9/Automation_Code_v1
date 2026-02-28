"""
Main script for Filteration Flask, Filteration Unit and Suction Pump control.
Runs homing (down until limit switch via PCF8574) and then movements.

Filteration flask uses same pins as stepper.py: STEP=18, DIR=23, EN=24 (BCM).
Filteration unit uses CLK=13, CW=19, EN=26 (BCM).
Suction pump uses separate GPIO pins (see suction_pump.py).
"""
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
    Suction_pump_up,
    Suction_pump_down,
    suction_pump_config,
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
    
    # Filteration unit: move down until limit switch on P2 (PCF8574) is pressed
    #filteration_unit_config()
    #Filteration_unit_up(200)
    # Filteration flask: move down until limit switch on P0 (PCF8574) is pressed
    #filteration_flask_config()
    #Filteration_flask_up(1150)

    # Suction pump: move down until limit switch on P1 (PCF8574) is pressed
    #suction_pump_config()
    #Suction_pump_up(1000)

    # Consumable: simple up/down movement without limit switch
    #Consumable_up(500)
    #Consumable_down(300)

    # Relays on second PCF8574: P0..P4 ON for 2 seconds each
    #run_relay_sequence()
    
    # Note: most relay boards map "Relay 1" to PCF pin P0.
    run_relay(P4, 3)
finally:
    # Clean up all modules
    filteration_cleanup()
    filteration_unit_cleanup()
    suction_cleanup()
    consumable_cleanup()
    relay_cleanup()
    GPIO.cleanup()
