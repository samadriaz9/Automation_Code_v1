import RPi.GPIO as GPIO
import time
import smbus

# Suction pump stepper motor pins (BCM numbering!)
# NOTE: update these BCM pins to match your wiring
# for your physical pins (e.g. 22 → its BCM GPIO, 30, 40, etc.).
STEP_PIN = 21   # CLK+
DIR_PIN = 12    # CW+
EN_PIN = 25     # EN+

# PCF8574 I2C expander (limit switch on P1)
PCF8574_ADDRESS = 0x20  # Adjust if your module uses a different address

delay = 0.001   # speed control

# One-time GPIO / I2C setup for this module
_initialized = False
_i2c_initialized = False
_bus = None


def _ensure_gpio():
    """Initialize GPIO for suction pump motor (once)."""
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


def _read_p1():
    """Read state of P1 from PCF8574 (returns 0 or 1)."""
    _ensure_i2c()
    value = _bus.read_byte(PCF8574_ADDRESS)
    return (value >> 1) & 0x01  # bit 1 is P1


def _step(steps, direction_high):
    """Run a given number of steps in one direction."""
    _ensure_gpio()
    GPIO.output(DIR_PIN, GPIO.HIGH if direction_high else GPIO.LOW)
    for _ in range(steps):
        GPIO.output(STEP_PIN, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(STEP_PIN, GPIO.LOW)
        time.sleep(delay)


def Suction_pump_up(steps):
    """Move suction pump motor UP by the given number of steps."""
    print(f"Suction pump: moving UP {steps} steps")
    # For this wiring, DIR HIGH corresponds to physical UP
    _step(steps, direction_high=True)


def Suction_pump_down(steps):
    """Move suction pump motor DOWN by the given number of steps."""
    print(f"Suction pump: moving DOWN {steps} steps")
    # For this wiring, DIR LOW corresponds to physical DOWN
    _step(steps, direction_high=False)


def suction_pump_config():
    """
    Drive the suction pump motor DOWN until the limit switch on P1 is pressed.

    Assumes P1 is pulled HIGH normally and goes LOW (0) when the switch is pressed.
    """
    print("Suction pump: homing DOWN until P1 limit switch (PCF8574) is pressed")
    _ensure_gpio()
    _ensure_i2c()

    # Set direction for DOWN (same as Suction_pump_down)
    GPIO.output(DIR_PIN, GPIO.LOW)

    while True:
        p1 = _read_p1()
        if p1 == 0:
            print("P1 limit switch detected, stopping.")
            break

        GPIO.output(STEP_PIN, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(STEP_PIN, GPIO.LOW)
        time.sleep(delay)


def cleanup():
    """Disable motor and release GPIO. Call when done with suction pump."""
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

