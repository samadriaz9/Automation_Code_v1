import RPi.GPIO as GPIO
import time
import smbus

# Media Dispensor motor pins (BCM numbering)
# Was 6 / 16 — changed to free pins (see PIN_MAP.md).
# Physical 40-pin header: GPIO24 -> pin 18 (STEP), GPIO27 -> pin 13 (DIR)
STEP_PIN = 24   # CLK+
DIR_PIN = 27    # CW+
# No EN pin — tie EN on driver hardware (GND if active-low enable)

# PCF8574 I2C expander (limit switch on P4)
PCF8574_ADDRESS = 0x20

delay = 0.001   # speed control

# One-time GPIO / I2C setup
_initialized = False
_i2c_initialized = False
_bus = None


def _ensure_gpio():
    """Initialize GPIO for media dispensor motor (once)."""
    global _initialized
    if not _initialized:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(STEP_PIN, GPIO.OUT)
        GPIO.setup(DIR_PIN, GPIO.OUT)
        _initialized = True


def _ensure_i2c():
    """Initialize I2C bus and PCF8574 (once)."""
    global _i2c_initialized, _bus
    if not _i2c_initialized:
        _bus = smbus.SMBus(1)

        # Set all pins as inputs with pull-ups
        _bus.write_byte(PCF8574_ADDRESS, 0xFF)

        _i2c_initialized = True


def _read_p4():
    """Read state of P4 from PCF8574 (returns 0 or 1)."""
    _ensure_i2c()
    value = _bus.read_byte(PCF8574_ADDRESS)
    return (value >> 4) & 0x01  # bit 4 = P4


def _step(steps, direction_high):
    """Run a given number of steps in one direction."""
    _ensure_gpio()
    GPIO.output(DIR_PIN, GPIO.HIGH if direction_high else GPIO.LOW)

    for _ in range(steps):
        GPIO.output(STEP_PIN, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(STEP_PIN, GPIO.LOW)
        time.sleep(delay)


def Media_dispensor_up(steps):
    """Move media dispensor motor UP by the given number of steps."""
    print(f"Media Dispensor: moving UP {steps} steps")
    _step(steps, direction_high=False)  # DIR LOW = UP


def Media_dispensor_down(steps):
    """Move media dispensor motor DOWN by the given number of steps."""
    print(f"Media Dispensor: moving DOWN {steps} steps")
    _step(steps, direction_high=True)  # DIR HIGH = DOWN


def Media_dispensor_home():
    """
    Drive the media dispensor motor DOWN until the limit switch on P4 is pressed.

    Wiring (corrected): P4 = 1 when not pressed (pull-up), P4 = 0 when pressed.
    """
    print("Media Dispensor: homing DOWN until P4 limit switch is pressed")

    _ensure_gpio()
    _ensure_i2c()

    # Same direction and step pattern as Media_dispensor_down()
    GPIO.output(DIR_PIN, GPIO.HIGH)

    while True:
        p4 = _read_p4()

        if p4 == 0:
            print("P4 limit switch detected, stopping.")
            break

        GPIO.output(STEP_PIN, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(STEP_PIN, GPIO.LOW)
        time.sleep(delay)


def cleanup():
    """Release I2C resources (GPIO cleanup handled by main)."""
    global _initialized, _i2c_initialized, _bus

    _initialized = False

    if _i2c_initialized and _bus is not None:
        try:
            _bus.close()
        except AttributeError:
            pass
        _i2c_initialized = False
        _bus = None