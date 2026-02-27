import RPi.GPIO as GPIO
import time

# Consumable stepper motor pins (BCM numbering)
EN_PIN = 14   # EN+
DIR_PIN = 15  # CW+
STEP_PIN = 17 # CLK+

delay = 0.001  # speed control

_initialized = False


def _ensure_gpio():
    """Initialize GPIO for consumable motor (once)."""
    global _initialized
    if not _initialized:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(STEP_PIN, GPIO.OUT)
        GPIO.setup(DIR_PIN, GPIO.OUT)
        GPIO.setup(EN_PIN, GPIO.OUT)

        GPIO.output(EN_PIN, GPIO.LOW)  # LOW = enable motor
        _initialized = True


def _step(steps, direction_high):
    """Run motor for given steps and direction."""
    _ensure_gpio()
    GPIO.output(DIR_PIN, GPIO.HIGH if direction_high else GPIO.LOW)

    for _ in range(steps):
        GPIO.output(STEP_PIN, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(STEP_PIN, GPIO.LOW)
        time.sleep(delay)


def consumable_up(steps):
    """Move consumable motor UP."""
    print(f"Consumable: moving UP {steps} steps")
    _step(steps, direction_high=True)


def consumable_down(steps):
    """Move consumable motor DOWN."""
    print(f"Consumable: moving DOWN {steps} steps")
    _step(steps, direction_high=False)


def cleanup():
    """Disable motor."""
    global _initialized
    if _initialized:
        GPIO.output(EN_PIN, GPIO.HIGH)  # disable motor
        _initialized = False