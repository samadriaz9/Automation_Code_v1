"""
Main script for Filteration Flask, Filteration Unit and Suction Pump control.
Runs homing (down until limit switch via PCF8574) and then movements.

Filteration flask: STEP=18, DIR=23 (BCM); EN tied on hardware (see filteration_flask.py).
Filteration unit: STEP=13, DIR=19 (BCM); EN tied on hardware (see filteration_unit.py).
Suction pump lift (stepper): STEP=21, DIR=12 (BCM); EN tied on hardware (see suction_pump_up_down.py). DC pump: suction_pump.py.
Petri dishes: STEP=10, DIR=22 (BCM); EN tied on hardware (see petri_dishes.py).
Media dispensor: STEP=24, DIR=27 (BCM); physical pins 18 & 13 (see Media_dispensor.py).
Suction pipe: STEP=8, DIR=20 (BCM); no limit switch — use up/down with steps only (see suction_pipe.py).

Shutdown: Ctrl+C runs full cleanup (see shutdown_all). SIGTERM (kill) also cleans up.
"""
import atexit
import signal
import sys
import time

from suction_pump_up_down import (
    suction_pump_up,
    suction_pump_down,
    suction_pump_home,
    cleanup as suction_lift_cleanup,
)
from filteration_flask import (  # pins 12 and 16 CLK+ + DIR+ only M1
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
    cleanup as filteration_suction_cleanup,
)

from petri_dishes import (
    petri_dishes_home,
    petri_dishes_up,
    petri_dishes_down,
    cleanup as petri_dishes_cleanup,
)
from camera_module import (
    Camera_home,
    Camera_up,
    Camera_down,
    cleanup as camera_cleanup,
)

from media_dispensor import (
    Media_dispensor_home,
    Media_dispensor_up,
    Media_dispensor_down,
    cleanup as media_dispensor_cleanup,
)

from suction_pipe import (
    suction_pipe_home,
    suction_pipe_up,
    suction_pipe_down,
    cleanup as suction_pipe_cleanup,
)

from solinoid_value import solenoid_valve_on, solenoid_valve_off, solenoid_valve, cleanup as solenoid_cleanup
import RPi.GPIO as GPIO

# --- Run once: stops PWM/relays/solenoid and releases GPIO (helps avoid drivers heating when idle) ---
_shutdown_done = False


def shutdown_all():
    """Idempotent full cleanup. Call on exit, Ctrl+C, or SIGTERM."""
    global _shutdown_done
    if _shutdown_done:
        return
    _shutdown_done = True
    print("\n[Shutdown] Releasing GPIO and stopping outputs...")

    # Stop DC/PWM and relays first; then stepper modules; solenoid off; GPIO.cleanup last.
    for name, fn in (
        ("filteration_suction_pump", filteration_suction_cleanup),
        ("suction_pump (DC)", suction_cleanup),
        ("suction_pump_up_down", suction_lift_cleanup),
        ("relay", relay_cleanup),
        ("solenoid", solenoid_cleanup),
        ("consumable", consumable_cleanup),
        ("filteration_flask", filteration_cleanup),
        ("filteration_unit", filteration_unit_cleanup),
        ("petri_dishes", petri_dishes_cleanup),
        ("camera", camera_cleanup),
        ("media_dispensor", media_dispensor_cleanup),
        ("suction_pipe", suction_pipe_cleanup),
    ):
        try:
            fn()
        except Exception as e:
            print(f"  Cleanup warning ({name}): {e}")

    try:
        GPIO.cleanup()
    except Exception:
        pass
    print("[Shutdown] Done.")


def _on_sigterm(signum, frame):
    shutdown_all()
    sys.exit(0)


# kill / systemd stop without -9
signal.signal(signal.SIGTERM, _on_sigterm)
atexit.register(shutdown_all)

try:
    x = input ('Enter 1: ')
    
    Media_dispensor_home()
    x= input ('Enter 2: ')
    
    Media_dispensor_up(3500)
    
    x = input ('Enter 3: ')
    Media_dispensor_down(800)
    
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
    x = input ('Enter 7: ')
    suction_pipe_up(100)

    x = input ('Enter 8: ')
    suction_pipe_down(100)

    
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
    

except KeyboardInterrupt:
    print("\nInterrupted (Ctrl+C).")

finally:
    shutdown_all()
