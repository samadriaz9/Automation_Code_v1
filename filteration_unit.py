import RPi.GPIO as GPIO
import time
import smbus

# Filteration Unit motor pins (BCM numbering)
STEP_PIN = 13   # CLK+
DIR_PIN = 19    # CW+
EN_PIN = 26     # EN+

# PCF8574 I2C expander (limit switch now on P6)
PCF8574_ADDRESS = 0x20  # Adjust if your module uses a different address

delay = 0.001   # speed control

# One-time GPIO / I2C setup for this module
_initialized = False
_i2c_initialized = False
_bus = None


def _ensure_gpio():
    """Initialize GPIO for filteration unit motor (once)."""
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

        # Configure all P0–P7 as inputs with pull-ups
        _bus.write_byte(PCF8574_ADDRESS, 0xFF)

        _i2c_initialized = True


def _read_p6():
    """Read state of P6 from PCF8574 (returns 0 or 1)."""
    _ensure_i2c()
    value = _bus.read_byte(PCF8574_ADDRESS)
    return (value >> 6) & 0x01  # ✅ bit 6 is P6


def _step(steps, direction_high):
    """Run a given number of steps in one direction."""
    _ensure_gpio()
    GPIO.output(DIR_PIN, GPIO.HIGH if direction_high else GPIO.LOW)

    for _ in range(steps):
        GPIO.output(STEP_PIN, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(STEP_PIN, GPIO.LOW)
        time.sleep(delay)


def Filteration_unit_up(steps):
    """Move filteration unit motor UP by the given number of steps."""
    print(f"Filteration Unit: moving UP {steps} steps")
    # assume DIR LOW = physical UP
    _step(steps, direction_high=False)


def Filteration_unit_down(steps):
    """Move filteration unit motor DOWN by the given number of steps."""
    print(f"Filteration Unit: moving DOWN {steps} steps")
    # assume DIR HIGH = physical DOWN
    _step(steps, direction_high=True)


def filteration_unit_config():
    """
    Drive the filteration unit motor DOWN until the limit switch on P6 is pressed.

    Assumes P6 is pulled HIGH normally and goes LOW (0) when the switch is pressed.
    """
    print("Filteration Unit: homing DOWN until P6 limit switch (PCF8574) is pressed")

    _ensure_gpio()
    _ensure_i2c()

    # Set direction for DOWN
    GPIO.output(DIR_PIN, GPIO.HIGH)

    while True:
        p6 = _read_p6()

        if p6 == 0:
            print("P6 limit switch detected, stopping.")
            break

        GPIO.output(STEP_PIN, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(STEP_PIN, GPIO.LOW)
        time.sleep(delay)


def cleanup():
    """Disable motor and release GPIO. Call when done with filteration unit."""
    global _initialized, _i2c_initialized, _bus

    if _initialized:
        GPIO.output(EN_PIN, GPIO.HIGH)  # disable driver
        _initialized = False

    if _i2c_initialized and _bus is not None:
        try:
            _bus.close()
        except AttributeError:
            pass
        _i2c_initialized = False
        _bus = None