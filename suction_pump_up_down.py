import RPi.GPIO as GPIO
import time
import smbus

# ---------- PIN MAP ----------
STEP_PIN = 21   # CLK+
DIR_PIN  = 12   # CW+
EN_PIN   = 25   # EN+

# PCF8574 (limit switch on P2)
PCF8574_ADDRESS = 0x20

delay = 0.001  # step speed

# Direction constants (easy to flip later if needed)
DIR_UP = GPIO.HIGH
DIR_DOWN = GPIO.LOW

_initialized = False
_i2c_initialized = False
_bus = None


# ---------- GPIO INIT ----------
def _ensure_gpio():
    """Initialize GPIO for suction pump lift motor (once)."""
    global _initialized
    if not _initialized:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(STEP_PIN, GPIO.OUT)
        GPIO.setup(DIR_PIN, GPIO.OUT)
        GPIO.setup(EN_PIN, GPIO.OUT)

        # LOW = enable
        GPIO.output(EN_PIN, GPIO.LOW)

        _initialized = True


# ---------- I2C INIT ----------
def _ensure_i2c():
    """Initialize I2C bus and PCF8574 (once)."""
    global _i2c_initialized, _bus
    if not _i2c_initialized:
        _bus = smbus.SMBus(1)
        _bus.write_byte(PCF8574_ADDRESS, 0xFF)  # all inputs (pull-ups)
        _i2c_initialized = True


def _read_p2():
    """Read limit switch on P2 (returns 0 or 1)."""
    _ensure_i2c()
    value = _bus.read_byte(PCF8574_ADDRESS)
    return (value >> 2) & 0x01  # bit 2 = P2


# ---------- STEP CORE ----------
def _step(steps, direction):
    """Run stepper for given steps."""
    _ensure_gpio()

    GPIO.output(DIR_PIN, direction)
    time.sleep(0.002)  # small settle time (important for some drivers)

    for _ in range(steps):
        GPIO.output(STEP_PIN, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(STEP_PIN, GPIO.LOW)
        time.sleep(delay)


# ---------- PUBLIC FUNCTIONS ----------
def suction_pump_up(steps):
    """Move suction pump UP."""
    print(f"Suction Pump: moving UP {steps} steps")
    _step(steps, DIR_UP)


def suction_pump_down(steps, stop_on_limit=True):
    """
    Move suction pump DOWN.
    If stop_on_limit=True, will stop early if P2 is hit.
    """
    print(f"Suction Pump: moving DOWN {steps} steps")

    _ensure_gpio()

    GPIO.output(DIR_PIN, DIR_DOWN)
    time.sleep(0.002)

    for _ in range(steps):
        if stop_on_limit and _read_p2() == 0:
            print("P2 limit reached during DOWN � stopping early.")
            break

        GPIO.output(STEP_PIN, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(STEP_PIN, GPIO.LOW)
        time.sleep(delay)


def suction_pump_home():
    """
    Move DOWN until P2 limit switch is pressed.
    Assumes P2 = HIGH normally, LOW when pressed.
    """
    print("Suction Pump: homing DOWN until P2 limit switch")

    _ensure_gpio()
    _ensure_i2c()

    GPIO.output(DIR_PIN, DIR_DOWN)
    time.sleep(0.002)

    while True:
        if _read_p2() == 0:
            print("P2 limit switch detected, stopping.")
            break

        GPIO.output(STEP_PIN, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(STEP_PIN, GPIO.LOW)
        time.sleep(delay)


# ---------- CLEANUP ----------
def cleanup():
    """Disable motor and release resources."""
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
