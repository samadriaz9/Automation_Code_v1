"""
Solenoid valve for filtration line (BCM numbering).

Uses GPIO 26 — this avoids UART TX (GPIO 14) which can sit HIGH at boot and energize the valve
before Python runs. Physical header pin 37.

Water-level sensor is read on GPIO 1 (pin 28). When level becomes HIGH, filtration solenoid is turned OFF.

See also: scripts/README_SOLENOID_BOOT.md if you need a boot-time LOW on this pin.
"""
import RPi.GPIO as GPIO
import time

# BCM
SOLENOID_PIN = 26
WATER_LEVEL_PIN = 1  # BCM, pin 28
WATER_LEVEL_ACTIVE_LOW = False  # Set True only if your sensor is active-LOW

_initialized = False


def _ensure_gpio():
    """Initialize GPIO once."""
    global _initialized

    if _initialized:
        return

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(SOLENOID_PIN, GPIO.OUT, initial=GPIO.LOW)
    # For 2-wire sensor wired to GND, keep input pulled HIGH when open.
    GPIO.setup(WATER_LEVEL_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
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


def water_level_reached():
    """Return True when level sensor input is HIGH."""
    _ensure_gpio()
    state = GPIO.input(WATER_LEVEL_PIN)
    if WATER_LEVEL_ACTIVE_LOW:
        return state == GPIO.LOW
    return state == GPIO.HIGH


def solinoid_value_to_filteration(seconds=None, timeout_seconds=120, poll_seconds=0.05):
    """
    Open filtration valve, then close.

    - If `seconds` is provided: timed behavior (legacy).
    - If `seconds` is None: keep valve ON until water level sensor is HIGH
      (or until timeout for safety).
    """
    _ensure_gpio()
    solinoid_value_to_filteration_on()
    try:
        if seconds is not None:
            time.sleep(max(0, float(seconds)))
            return

        timeout_seconds = max(0, float(timeout_seconds))
        poll_seconds = max(0.01, float(poll_seconds))
        start = time.time()

        while True:
            if water_level_reached():
                print("Water level reached -> Filtration solenoid OFF")
                break
            if timeout_seconds and (time.time() - start) >= timeout_seconds:
                print("Filtration solenoid timeout -> OFF")
                break
            time.sleep(poll_seconds)
    finally:
        solinoid_value_to_filteration_off()


def cleanup():
    """Ensure valve off; GPIO.cleanup handled in main."""
    global _initialized
    if _initialized:
        GPIO.output(SOLENOID_PIN, GPIO.LOW)
        _initialized = False
