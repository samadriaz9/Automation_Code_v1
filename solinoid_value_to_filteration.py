"""
Solenoid valve for filtration line (BCM numbering).

Uses GPIO 26 — this avoids UART TX (GPIO 14) which can sit HIGH at boot and energize the valve
before Python runs. Physical header pin 37.

See also: scripts/README_SOLENOID_BOOT.md if you need a boot-time LOW on this pin.
"""
import RPi.GPIO as GPIO
import time

# BCM
SOLENOID_PIN = 26

_initialized = False


def _ensure_gpio():
    """Initialize GPIO once."""
    global _initialized

    if _initialized:
        return

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(SOLENOID_PIN, GPIO.OUT, initial=GPIO.LOW)
    _initialized = True


def solinoid_value_to_filteration_on():
    """Open solenoid valve (filtration)."""
    _ensure_gpio()
    print("Filtration solenoid valve ON")
    GPIO.output(SOLENOID_PIN, GPIO.HIGH)


def solinoid_value_to_filteration_off():
    """Close solenoid valve (filtration)."""
    if _initialized:
        print("Filtration solenoid valve OFF")
        GPIO.output(SOLENOID_PIN, GPIO.LOW)


def solinoid_value_to_filteration(seconds):
    """Open valve for given seconds, then close."""
    seconds = max(0, float(seconds))
    solinoid_value_to_filteration_on()
    time.sleep(seconds)
    solinoid_value_to_filteration_off()


def cleanup():
    """Ensure valve off; GPIO.cleanup handled in main."""
    global _initialized
    if _initialized:
        GPIO.output(SOLENOID_PIN, GPIO.LOW)
        _initialized = False
