"""
Main script for Filteration Flask, Filteration Unit and Suction Pump control.
Runs homing (down until limit switch via PCF8574) and then movements.

Filteration flask: STEP=18, DIR=23 (BCM); EN tied on hardware (see filteration_flask.py).
Filteration unit: STEP=13, DIR=19 (BCM); EN tied on hardware (see filteration_unit.py).
Suction pump lift (stepper): STEP=21, DIR=12 (BCM); EN tied on hardware (see suction_pump_up_down.py). Flask/upper DC pump: GPIO 11 RPWM (see upper_suction_pump.py); leave GPIO 4 for DS18B20.
Petri dishes: STEP=10, DIR=22 (BCM); EN tied on hardware (see petri_dishes.py).
Media dispensor: STEP=24, DIR=27 (BCM); physical pins 18 & 13 (see Media_dispensor.py).
Suction pipe: STEP=8, DIR=20 (BCM); no limit switch — use up/down with steps only (see suction_pipe.py).
Incubator lid: STEP=6, DIR=16 (BCM); physical pins 31 & 36; no limit (see incubator_lid.py).
Filtration solenoid: GPIO 26 (BCM), pin 37 (see solinoid_value_to_filteration.py).

Shutdown: Ctrl+C runs full cleanup (see shutdown_all). SIGTERM (kill) also cleans up.
"""
import atexit
import gc
from pdb import run
import signal
import sys
import time
import cv2

import filteration_suction_pump
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
from upper_suction_pump import (
    upper_suction_pump,
    upper_suction_pump_on,
    upper_suction_pump_off,
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
from incubation_module import Start_incubation
from imaging import start_imaging_capture_pattern

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

from incubator_lid import (
    incubator_lid_home,
    incubator_lid_up,
    incubator_lid_down,
    cleanup as incubator_lid_cleanup,
)
from usb_camera_thread import start_usb_camera_thread, stop_usb_camera_thread

from solinoid_value_to_filteration import (
    solinoid_value_to_filteration,
    solinoid_value_to_filteration_on,
    solinoid_value_to_filteration_off,
    water_level_reached,
    cleanup as solenoid_cleanup,
)
from solinoid_value_drain import (
    solinoid_value_drain,
    solinoid_value_drain_on,
    solinoid_value_drain_off,
    cleanup as drain_solenoid_cleanup,
)
from solinoid_waste import (
    solinoid_waste,
    solinoid_waste_on,
    solinoid_waste_off,
    cleanup as waste_solenoid_cleanup,
)
import RPi.GPIO as GPIO

# --- Run once: stops PWM/relays/solenoid and releases GPIO (helps avoid drivers heating when idle) ---
_shutdown_done = False
_usb_camera_worker = None


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
    ("upper_suction_pump (DC)", suction_cleanup),
        ("suction_pump_up_down", suction_lift_cleanup),
        ("relay", relay_cleanup),
        ("solenoid", solenoid_cleanup),
        ("drain_solenoid", drain_solenoid_cleanup),
        ("waste_solenoid", waste_solenoid_cleanup),
        ("consumable", consumable_cleanup),
        ("filteration_flask", filteration_cleanup),
        ("filteration_unit", filteration_unit_cleanup),
        ("petri_dishes", petri_dishes_cleanup),
        ("camera", camera_cleanup),
        ("media_dispensor", media_dispensor_cleanup),
        ("suction_pipe", suction_pipe_cleanup),
        ("incubator_lid", incubator_lid_cleanup),
    ):
        try:
            fn()
        except Exception as e:
            print(f"  Cleanup warning ({name}): {e}")

    # Finalize PWM wrappers while GPIO is still valid (avoids RPi.GPIO PWM.__del__ after cleanup).
    gc.collect()

    try:
        GPIO.cleanup()
    except Exception:
        pass
    print("[Shutdown] Done.")


def _on_sigterm(signum, frame):
    shutdown_all()
    sys.exit(0)


# kill / systemd stop without -9 This is the kill signal handler
signal.signal(signal.SIGTERM, _on_sigterm)
atexit.register(shutdown_all)

try:
    x = input ('Enter to home all modules: ')
    x = input ('Enter to put media pad in trash: ')
    incubator_lid_home()
    petri_dishes_home()
    petri_dishes_down(1025)
    suction_pipe_home()
    suction_pump_home()
    suction_pump_up(3055)
    suction_pipe_up(1010)
    upper_suction_pump_on(100)
    time.sleep(2)
    suction_pipe_home()
    suction_pump_down(930)
    upper_suction_pump_off()
    suction_pipe_up(800)
    for i in range(20):
        suction_pump_up(120)
        suction_pump_down(120)
        time.sleep(0.01)
    time.sleep(2)

    x = input ('home: ?')
    incubator_lid_home()
    petri_dishes_home()
    petri_dishes_down(3290)
    incubator_lid_up(200)




    x = input ('Enter TO START MACHINE : ')
   
    x = input ('Enter for media despensor home: ')
    Media_dispensor_home()
    x= input ('Enter for media dispensor move up: ')
    Media_dispensor_up(3500)
    x = input ('Put in the syringe containging media: ')
    Media_dispensor_down(800)
    
    
    x = input ("Enter to bring petri dishes home")
    incubator_lid_home()
    petri_dishes_home()
    petri_dishes_down(1035)
    
    x = input ("1. Enter to put filter paper on filteration flask")
    suction_pipe_home()
    suction_pump_home()
    filteration_unit_config()
    filteration_flask_config()
    Filteration_flask_up(1140)
    suction_pipe_up(1010)
    upper_suction_pump_on(22)
    time.sleep(3)
    suction_pipe_down(50)
    for i in range(10):
        suction_pump_up(3)
        suction_pump_down(3)
        time.sleep(0.01)
    time.sleep(1)
    suction_pipe_down(1010)
    suction_pump_up(1245)
    filteration_suction_pump_on(100)
    upper_suction_pump_off()
    suction_pipe_up(600)
    time.sleep(2)
    filteration_suction_pump_on(20)
    suction_pipe_home()

    x = input ("2. Enter to send filter paper to assembly")
    filteration_unit_config()
    filteration_flask_config()
    Filteration_flask_up(32)
    Filteration_unit_up(850)
    time.sleep(1)
    solinoid_value_to_filteration()
    filteration_suction_pump_on(90)
    time.sleep(20)
    while water_level_reached():
        filteration_suction_pump_off()
        print(
            "Water level sensor still reads FULL after filtration pump run — pump may not be drawing. "
            "Fix the pump or plumbing before continuing."
        )
        input("Press Enter after fixing to re-run pump (90% for 20 s) and re-check...")
        filteration_suction_pump_on(90)
        time.sleep(20)

    filteration_suction_pump_off()
    
    x = input ("3. Enter for picking up media pad plus petri dishes")
    suction_pump_home()
    suction_pipe_home()
    suction_pipe_up(1025)
    upper_suction_pump_on(100)
    time.sleep(2)
    suction_pipe_down(1025)
    suction_pump_up(3055)
    suction_pipe_up(300)
    upper_suction_pump_off()
    
    x = input ("4. Enter for poruing media")
    petri_dishes_home()
    petri_dishes_down(300)
    Media_dispensor_down(800)
    time.sleep(2)
    petri_dishes_down(725)
    
    
    x = input ("5. Enter to pick up filteration unit")
    filteration_unit_config()
    filteration_flask_config()
    Filteration_flask_up(1130)
    
    
    x = input ("6. Picking up filter paper from filteration flask")
    suction_pipe_home()
    suction_pump_home()
    suction_pump_up(1245)
    suction_pipe_up(670)
    upper_suction_pump_on(30)
    time.sleep(3)
    suction_pipe_down(670)
    suction_pump_up(1805)
    suction_pipe_up(710)
    upper_suction_pump_off()
    time.sleep(3)
    suction_pipe_home()
    
    x = input ("7. Enter to shift it for incubation")
    incubator_lid_home()
    petri_dishes_home()
    petri_dishes_down(3280)
    incubator_lid_up(200)
    
    x = input ("8. Enter to start incubation")
    run_relay(P1, 1)
    Start_incubation(37, 1)

    x  = input ("9. Enter to start pictures")
    
    try:
        cap = cv2.VideoCapture(0)
        ok, frame = cap.read()
        if ok:
            run_relay(P7, 3)
            time.sleep(3)
            print("camera off")
    except Exception as e:
        print(f"Camera not found")
        sys.exit(1)

    Camera_home()
    Camera_down(2430)
    incubator_lid_home()
    petri_dishes_home()
    petri_dishes_down(3290)
    petri_dishes_up(330)
    ok, frame = cap.read()
    if ok:
        print("Camera is on")
    else:
        run_relay(P7, 3)
        print("Camera switch on")
    time.sleep(3)
    print("Wanna do configuration for camera? (y/n)")
    yn = input()
    if yn == "y":
        _usb_camera_worker = start_usb_camera_thread(device_index=0)
        print("press y again when camera is configured")
        yn = input()
        if yn == "y":
            # Stop the preview thread so imaging can open the camera device.
            stop_usb_camera_thread(_usb_camera_worker)
            _usb_camera_worker = None
            time.sleep(0.5)
    
    if ok:
        print("Starting imaging capture pattern")
        start_imaging_capture_pattern()
        time.sleep(0.5)
        print("Imaging capture pattern completed")
    
    print("Moving petri dishes home")
    petri_dishes_home()
    print("Moving petri dishes down")
    petri_dishes_down(3290)
    print("Moving incubator lid up")
    incubator_lid_up(200)
    run_relay(P7, 3)
    time.sleep(3)


    x = input ('Enter to put filter paper in trash: ')
    incubator_lid_home()
    petri_dishes_home()
    petri_dishes_down(1025)
    suction_pipe_home()
    suction_pump_home()
    suction_pump_up(3055)
    suction_pipe_up(1010)
    upper_suction_pump_on(100)
    time.sleep(2)
    suction_pipe_home()
    suction_pump_down(930)
    upper_suction_pump_off()
    suction_pipe_up(800)
    for i in range(20):
        suction_pump_up(120)
        suction_pump_down(120)
        time.sleep(0.01)
    time.sleep(2)







except KeyboardInterrupt:
    print("\nInterrupted (Ctrl+C).")

finally:
    stop_usb_camera_thread(_usb_camera_worker)
    shutdown_all()
