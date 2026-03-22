"""
Suction pipe stepper — STEP + DIR only (no EN in software), like consumable.py.

No limit switch on this axis: only use suction_pipe_up / suction_pipe_down with a step count.
Hardware: tie EN on the driver to GND (or per datasheet).

BCM: STEP=8 (physical pin 24), DIR=20 (physical pin 38).
"""
import RPi.GPIO as GPIO
import time

STEP_PIN = 8    # CLK+
DIR_PIN = 20    # CW+

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


def suction_pipe_up(steps):
    """Move suction pipe UP by the given number of steps."""
    print(f"Suction Pipe: moving UP {steps} steps")
    _step(steps, direction_high=False)  # DIR LOW = physical UP


def suction_pipe_down(steps):
    """Move suction pipe DOWN by the given number of steps."""
    print(f"Suction Pipe: moving DOWN {steps} steps")
    _step(steps, direction_high=True)  # DIR HIGH = physical DOWN


def suction_pipe_home():
    """
    No limit switch is wired for this module — homing does nothing.

    If you add a PCF8574 input later, implement homing here (see petri_dishes.py).
    """
    print("Suction Pipe: no limit switch configured — suction_pipe_home() skipped.")


# Aliases (optional)
Suction_Pipe_up = suction_pipe_up
Suction_Pipe_down = suction_pipe_down
Suction_Pipe_home = suction_pipe_home


def cleanup():
    """Release state (GPIO cleanup handled by main)."""
    global _initialized
    if _initialized:
        _initialized = False
