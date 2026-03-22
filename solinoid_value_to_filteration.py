"""
Solenoid valve for filtration line (BCM numbering).

Uses GPIO 26 — avoids GPIO 14 (UART TX), which can sit HIGH at boot and energize the valve
before Python runs. Physical header pin 37.

See also: scripts/README_SOLENOID_BOOT.md if you need a boot-time LOW on this pin.
"""
import RPi.GPIO as GPIO
import time

# BCM — general-purpose; not UART/SPI/I2C
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


def solenoid_valve_on():
    """Open solenoid valve (filtration)."""
    _ensure_gpio()
    print("Filtration solenoid valve ON")
    GPIO.output(SOLENOID_PIN, GPIO.HIGH)


def solenoid_valve_off():
    """Close solenoid valve (filtration)."""
    if _initialized:
        print("Filtration solenoid valve OFF")
        GPIO.output(SOLENOID_PIN, GPIO.LOW)


def solenoid_valve(seconds):
    """Open valve for given seconds."""
    seconds = max(0, float(seconds))
    solenoid_valve_on()
    time.sleep(seconds)
    solenoid_valve_off()


def cleanup():
    """Ensure valve off; GPIO.cleanup handled in main."""
    global _initialized
    if _initialized:
        GPIO.output(SOLENOID_PIN, GPIO.LOW)
        _initialized = False
