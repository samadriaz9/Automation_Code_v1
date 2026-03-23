"""
Solenoid valve for waste line (BCM numbering).

Default pin:
- SOLENOID_PIN = GPIO 0 (pin 27)
"""

import RPi.GPIO as GPIO
import time

SOLENOID_PIN = 0
_initialized = False


def _ensure_gpio():
    """Initialize GPIO once."""
    global _initialized
    if _initialized:
        return

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(SOLENOID_PIN, GPIO.OUT, initial=GPIO.LOW)
    _initialized = True


def solinoid_waste_on():
    """Open waste solenoid valve."""
    _ensure_gpio()
    print("Waste solenoid valve ON")
    GPIO.output(SOLENOID_PIN, GPIO.HIGH)


def solinoid_waste_off():
    """Close waste solenoid valve."""
    if _initialized:
        print("Waste solenoid valve OFF")
        GPIO.output(SOLENOID_PIN, GPIO.LOW)


def solinoid_waste(seconds):
    """Open waste solenoid for given seconds, then close."""
    seconds = max(0, float(seconds))
    solinoid_waste_on()
    time.sleep(seconds)
    solinoid_waste_off()


def cleanup():
    """Ensure OFF; GPIO.cleanup handled in main."""
    global _initialized
    if _initialized:
        GPIO.output(SOLENOID_PIN, GPIO.LOW)
        _initialized = False

