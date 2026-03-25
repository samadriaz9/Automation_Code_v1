"""
Incubator lid stepper — STEP + DIR only (no EN in software), same pattern as suction_pipe.py.

No limit switch: use incubator_lid_up / incubator_lid_down with a step count.
Hardware: tie EN on the driver to GND (or per datasheet).

BCM: STEP=6 (physical pin 31), DIR=16 (physical pin 36).
"""
import RPi.GPIO as GPIO
import time

STEP_PIN = 6    # CLK+
DIR_PIN = 16    # CW+

delay = 0.001

_initialized = False


def _ensure_gpio():
    global _initialized
    if not _initialized:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(STEP_PIN, GPIO.OUT)
        GPIO.setup(DIR_PIN, GPIO.OUT)
        _initialized = True


def _step(steps, direction_high):
    _ensure_gpio()
    GPIO.output(DIR_PIN, GPIO.HIGH if direction_high else GPIO.LOW)
    for _ in range(steps):
        GPIO.output(STEP_PIN, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(STEP_PIN, GPIO.LOW)
        time.sleep(delay)


def incubator_lid_up(steps):
    """Move incubator lid UP by the given number of steps."""
    print(f"Incubator lid: moving UP {steps} steps")
    _step(steps, direction_high=True)  # DIR LOW = physical UP (same as suction_pipe)


def incubator_lid_down(steps):
    """Move incubator lid DOWN by the given number of steps."""
    print(f"Incubator lid: moving DOWN {steps} steps")
    _step(steps, direction_high=True)  # DIR HIGH = physical DOWN


def incubator_lid_home():
    """No limit switch — no homing. Add PCF8574 logic later if needed."""
    print("Incubator lid: no limit switch configured — incubator_lid_home() skipped.")


# Optional CamelCase aliases
Incubator_lid_up = incubator_lid_up
Incubator_lid_down = incubator_lid_down
Incubator_lid_home = incubator_lid_home


def cleanup():
    """Release state (GPIO cleanup handled by main)."""
    global _initialized
    if _initialized:
        _initialized = False
