"""
Solenoid valve control (BCM numbering).

BOOT NOTE — valve turning ON before main.py runs:
  GPIO 14 is the UART TX pin. With the serial console enabled, this line is
  often HIGH at boot, which turns ON an active-HIGH driver/relay before Python runs.

  Fix: install scripts/solenoid_boot_safe.sh + systemd service (see scripts/README_SOLENOID_BOOT.md),
  or move the solenoid to a non-UART GPIO (e.g. 17, 22) and set SOLENOID_PIN below.

"""
import RPi.GPIO as GPIO
import time

# ---------- PIN SETUP ----------
# BCM. Avoid 14/15 if you need UART-free pins; 14 conflicts with UART TX at boot.
SOLENOID_PIN = 14

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