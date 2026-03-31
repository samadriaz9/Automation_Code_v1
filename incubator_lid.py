"""
Incubator lid stepper control (direct GPIO STEP + DIR).

- STEP uses GPIO6 (physical pin 31)
- DIR/CW+ uses GPIO14 (physical pin 8)
- No limit switch logic in this module

Hardware: tie EN on the driver to GND (or per datasheet).
"""
import RPi.GPIO as GPIO
import time

STEP_PIN = 6    # CLK+
DIR_PIN = 14    # CW+ (pin 8)

delay = 0.001

_initialized = False


def _ensure_gpio():
    global _initialized
    if not _initialized:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(STEP_PIN, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(DIR_PIN, GPIO.OUT, initial=GPIO.LOW)
        _initialized = True


def _step(steps, direction_high):
    _ensure_gpio()
    GPIO.output(DIR_PIN, GPIO.HIGH if direction_high else GPIO.LOW)
    # Some stepper drivers need a short DIR setup time before the first step edge.
    time.sleep(delay)
    for _ in range(steps):
        GPIO.output(STEP_PIN, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(STEP_PIN, GPIO.LOW)
        time.sleep(delay)


def incubator_lid_up(steps):
    """Move incubator lid UP by the given number of steps."""
    print(f"Incubator lid: moving UP {steps} steps (DIR=GPIO14 HIGH)")
    _step(steps, direction_high=True)


def incubator_lid_down(steps):
    """Move incubator lid DOWN by the given number of steps."""
    print(f"Incubator lid: moving DOWN {steps} steps (DIR=GPIO14 LOW)")
    _step(steps, direction_high=False)


def incubator_lid_home():
    """No limit switch — no homing."""
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
