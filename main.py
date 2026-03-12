"""
Main script for Filteration Flask, Filteration Unit and Suction Pump control.
Runs homing (down until limit switch via PCF8574) and then movements.

Filteration flask uses same pins as stepper.py: STEP=18, DIR=23, EN=24 (BCM).
Filteration unit uses CLK=13, CW=19, EN=26 (BCM).
Suction pump uses separate GPIO pins (see suction_pump.py).
"""
import time
from suction_pump_up_down import (suction_pump_up,
 suction_pump_down, suction_pump_home
)
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
    suction_pump,suction_pump_on, suction_pump_off,
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

from filteration_suction_pump import (
    filteration_suction_pump_on,
    filteration_suction_pump_off,
)

from petri_dishes import (
    petri_dishes_home,
    petri_dishes_up,
    petri_dishes_down,
)
from camera_module import (
    Camera_home,
    Camera_up,
    Camera_down,
)

from media_dispensor import (
    Media_dispensor_home,
    Media_dispensor_up,
    Media_dispensor_down,
)

from solinoid_value import solenoid_valve_on, solenoid_valve_off, solenoid_valve
import RPi.GPIO as GPIO
import time

try:
    solenoid_valve(0.1)
    x = input ('Enter 1: ')
    
    Media_dispensor_home()
    x= input ('Enter 2: ')
    
    Media_dispensor_down(3500)
    
    x = input ('Enter 3: ')
    Media_dispensor_up(800)
    
    x = input ('Enter 4: ')
    Consumable_down(400)
    x = input ('Enter 5: ')
    Consumable_up(400)
    
    x = input ('Enter 5: ')
    petri_dishes_home()
    petri_dishes_down(1870)
    
    Camera_home()
    Camera_down(2500)
    
    
    x= input ('Enter 6: ')
    #media pad + petri dish
    suction_pump_home()   # step 1
    suction_pump_up(250)  # step 2
    
    x = input ("Enter 7: ")
    filteration_unit_config()
    filteration_flask_config()
    Filteration_flask_up(1150)
    
    x = input ("Enter 7: ")
    
    Consumable_up(290)    # step 3
    suction_pump_on(100)
    time.sleep(1)
    suction_pump_up(3110)
    suction_pump_off()
    Consumable_down(290)
    
    x = input ("Enter 8: ")
    
    petri_dishes_down(800)
    Media_dispensor_up(520)
    petri_dishes_up(800)
    
    x = input ("Enter 9: ")
    #  Filter Paper
    Consumable_up(290)
    suction_pump_home()
    suction_pump_up(420)
    Consumable_up(310)
    suction_pump_on(35)
    time.sleep(2)
    Consumable_down(310)
    suction_pump_up(1220)
    suction_pump_off()
    Consumable_down(290)
    
    x = input ("Enter 10: ")
    filteration_suction_pump_on(90)
    time.sleep(2)
    filteration_suction_pump_off()
    
    filteration_unit_config()
    filteration_flask_config()
    Filteration_flask_up(32)
    Filteration_unit_up(850)
    
    
    #solinoid
    x= input ("Enter 11: ")
    solenoid_valve(2)
    
    x = input ("Enter 12: ")
    filteration_suction_pump_on(90)
    time.sleep(5) 
    filteration_suction_pump_off()
    
    x = input ("Enter 13: ")
    filteration_unit_config()
    Filteration_flask_up(1150)
    
    
    x= input ("Enter 12: ") #carefully observe
    suction_pump_on(100)
    time.sleep(5)
    suction_pump_up(1820)
    suction_pump_off()
    time.sleep(3)
    suction_pump_down(1820)
    
    x = input ("Enter 13: ")
    petri_dishes_home()
    Camera_up(500)
    Camera_down(500)
    

finally:
    # Clean up all modules
    filteration_cleanup()
    filteration_unit_cleanup()
    suction_cleanup()
    consumable_cleanup()
    relay_cleanup()
    GPIO.cleanup()
