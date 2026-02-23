import RPi.GPIO as GPIO
import time

# Media Dispenser motor pins (same as stepper.py)
STEP_PIN = 18   # CLK+
DIR_PIN = 23    # CW+
EN_PIN = 24     # EN+

# No limit switches for this motor

delay = 0.001   # speed control (same as stepper.py)

# One-time GPIO setup for this module
_initialized = False


def _ensure_gpio():
    """Initialize GPIO for media dispenser motor (once)."""
    global _initialized
    if not _initialized:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(STEP_PIN, GPIO.OUT)
        GPIO.setup(DIR_PIN, GPIO.OUT)
        GPIO.setup(EN_PIN, GPIO.OUT)
        GPIO.output(EN_PIN, GPIO.LOW)  # Enable motor (LOW = enable)
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


def Media_Disperensor_up(steps):
    """Move media dispenser motor UP by the given number of steps."""
    print(f"Media Dispenser: moving UP {steps} steps")
    _step(steps, direction_high=True)


def Media_Disperensor_down(steps):
    """Move media dispenser motor DOWN by the given number of steps."""
    print(f"Media Dispenser: moving DOWN {steps} steps")
    _step(steps, direction_high=False)


def cleanup():
    """Disable motor and release GPIO. Call when done with dispenser."""
    global _initialized
    if _initialized:
        GPIO.output(EN_PIN, GPIO.HIGH)
        # Only cleanup if this module did the setup (optional: skip if stepper.py also uses GPIO)
        # GPIO.cleanup()
        _initialized = False
