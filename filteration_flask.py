import RPi.GPIO as GPIO
import time
import smbus

# Filteration Flask motor pins (same as stepper.py)
STEP_PIN = 18   # CLK+
DIR_PIN = 23    # CW+
EN_PIN = 24     # EN+

# PCF8574 I2C expander (limit switch on P0)
PCF8574_ADDRESS = 0x20  # Adjust if your module uses a different address

delay = 0.001   # speed control (same as stepper.py)

# One-time GPIO / I2C setup for this module
_initialized = False
_i2c_initialized = False
_bus = None


def _ensure_gpio():
    """Initialize GPIO for filteration flask motor (once)."""
    global _initialized
    if not _initialized:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(STEP_PIN, GPIO.OUT)
        GPIO.setup(DIR_PIN, GPIO.OUT)
        GPIO.setup(EN_PIN, GPIO.OUT)
        GPIO.output(EN_PIN, GPIO.LOW)  # Enable motor (LOW = enable)
        _initialized = True


def _ensure_i2c():
    """Initialize I2C bus and PCF8574 (once)."""
    global _i2c_initialized, _bus
    if not _i2c_initialized:
        _bus = smbus.SMBus(1)  # I2C bus 1 on Raspberry Pi
        # Configure all P0–P7 as inputs with internal pull-ups (write 1s)
        _bus.write_byte(PCF8574_ADDRESS, 0xFF)
        _i2c_initialized = True


def _read_p0():
    """Read state of P0 from PCF8574 (returns 0 or 1)."""
    _ensure_i2c()
    value = _bus.read_byte(PCF8574_ADDRESS)
    return value & 0x01  # bit 0 is P0


def _step(steps, direction_high):
    """Run a given number of steps in one direction."""
    _ensure_gpio()
    GPIO.output(DIR_PIN, GPIO.HIGH if direction_high else GPIO.LOW)
    for _ in range(steps):
        GPIO.output(STEP_PIN, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(STEP_PIN, GPIO.LOW)
        time.sleep(delay)


def Filteration_flask_up(steps):
    """Move filteration flask motor UP by the given number of steps."""
    print(f"Filteration Flask: moving UP {steps} steps")
    # For this wiring, DIR LOW corresponds to physical UP
    _step(steps, direction_high=False)


def Filteration_flask_down(steps):
    """Move filteration flask motor DOWN by the given number of steps."""
    print(f"Filteration Flask: moving DOWN {steps} steps")
    # For this wiring, DIR HIGH corresponds to physical DOWN
    _step(steps, direction_high=True)


def filteration_flask_config():
    """
    Drive the filteration flask motor DOWN until the limit switch on P0 is pressed.

    Assumes P0 is pulled HIGH normally and goes LOW (0) when the switch is pressed.
    """
    print("Filteration Flask: homing DOWN until P0 limit switch (PCF8574) is pressed")
    _ensure_gpio()
    _ensure_i2c()

    # Set direction for DOWN (same as Filteration_flask_down)
    GPIO.output(DIR_PIN, GPIO.HIGH)

    while True:
        p0 = _read_p0()
        if p0 == 0:
            print("P0 limit switch detected, stopping.")
            break

        GPIO.output(STEP_PIN, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(STEP_PIN, GPIO.LOW)
        time.sleep(delay)


def cleanup():
    """Disable motor and release GPIO. Call when done with filteration flask."""
    global _initialized, _i2c_initialized, _bus
    if _initialized:
        GPIO.output(EN_PIN, GPIO.HIGH)
        _initialized = False
    if _i2c_initialized and _bus is not None:
        try:
            _bus.close()
        except AttributeError:
            # smbus on some systems may not have close()
            pass
        _i2c_initialized = False
        _bus = None

