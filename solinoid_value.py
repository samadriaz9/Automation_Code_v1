import RPi.GPIO as GPIO
import time

# ---------- PIN SETUP ----------
SOLENOID_PIN = 14  # BCM

_initialized = False


def _ensure_gpio():
    """Initialize GPIO once."""
    global _initialized

    if _initialized:
        return

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(SOLENOID_PIN, GPIO.OUT, initial=GPIO.LOW)
    _initialized = True


# ✅ valve ON
def solenoid_valve_on():
    """Open solenoid valve."""
    _ensure_gpio()
    print("Solenoid valve ON")
    GPIO.output(SOLENOID_PIN, GPIO.HIGH)


# ✅ valve OFF
def solenoid_valve_off():
    """Close solenoid valve."""
    if _initialized:
        print("Solenoid valve OFF")
        GPIO.output(SOLENOID_PIN, GPIO.LOW)


# ✅ timed run (optional helper)
def solenoid_valve(seconds):
    """Open valve for given seconds."""
    seconds = max(0, float(seconds))
    solenoid_valve_on()
    time.sleep(seconds)
    solenoid_valve_off()


def cleanup():
    """Cleanup flag only (GPIO.cleanup handled in main)."""
    global _initialized
    if _initialized:
        GPIO.output(SOLENOID_PIN, GPIO.LOW)
        _initialized = False