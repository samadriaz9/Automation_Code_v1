"""
Solenoid valve for drain line (BCM numbering).

This module mirrors `solinoid_value_to_filteration.py`:
- `solinoid_value_drain_on()` / `solinoid_value_drain_off()`
- `solinoid_value_drain(seconds)` timed pulse
- `cleanup()` to force OFF (GPIO.cleanup handled in `main.py`)
"""

import RPi.GPIO as GPIO
import time

# BCM — picked as a free pin in the current map.
SOLENOID_PIN = 9  # physical header pin 21

_initialized = False


def _ensure_gpio():
    """Initialize GPIO once."""
    global _initialized

    if _initialized:
        return

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(SOLENOID_PIN, GPIO.OUT, initial=GPIO.LOW)
    _initialized = True


def solinoid_value_drain_on():
    """Open drain solenoid."""
    _ensure_gpio()
    print("Drain solenoid valve ON")
    GPIO.output(SOLENOID_PIN, GPIO.HIGH)


def solinoid_value_drain_off():
    """Close drain solenoid."""
    if _initialized:
        print("Drain solenoid valve OFF")
        GPIO.output(SOLENOID_PIN, GPIO.LOW)


def solinoid_value_drain(seconds):
    """Open valve for given seconds, then close."""
    seconds = max(0, float(seconds))
    solinoid_value_drain_on()
    time.sleep(seconds)
    solinoid_value_drain_off()


def cleanup():
    """Ensure valve off; GPIO.cleanup handled in main."""
    global _initialized
    if _initialized:
        GPIO.output(SOLENOID_PIN, GPIO.LOW)
        _initialized = False

