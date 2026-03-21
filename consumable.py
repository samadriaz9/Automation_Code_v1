import RPi.GPIO as GPIO
import time

# Consumable stepper motor pins (BCM) — STEP + DIR only (frees GPIO 14 for solenoid / other use).
# Hardware: tie EN+ on the driver to GND (typical: EN active-LOW).
STEP_PIN = 17   # CLK+
DIR_PIN = 15    # CW+

delay = 0.001   # speed control

_initialized = False


def _ensure_gpio():
    """Initialize GPIO for consumable motor (once)."""
    global _initialized
    if not _initialized:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(STEP_PIN, GPIO.OUT)
        GPIO.setup(DIR_PIN, GPIO.OUT)
        _initialized = True


def _step(steps, direction_high):
    """Run a given number of steps in one direction."""
    _ensure_gpio()
    GPIO.output(DIR_PIN, GPIO.HIGH if direction_high else GPIO.LOW)
    for _ in range(steps):
        GPIO.output(STEP_PIN, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(STEP_PIN, GPIO.LOW)
        time.sleep(delay)


def Consumable_up(steps):
    """Move consumable motor UP by the given number of steps."""
    print(f"Consumable: moving UP {steps} steps")
    # Assume DIR LOW = physical UP (same convention as filteration flask)
    _step(steps, direction_high=False)


def Consumable_down(steps):
    """Move consumable motor DOWN by the given number of steps."""
    print(f"Consumable: moving DOWN {steps} steps")
    _step(steps, direction_high=True)


def cleanup():
    """Release state (GPIO cleanup handled by main). No EN pin."""
    global _initialized
    if _initialized:
        _initialized = False

