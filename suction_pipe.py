"""
Suction pipe stepper — STEP + DIR only (no EN in software), like consumable.py.

Limit switch support:
- New limit switch is wired to the second I2C expander (PCF8574) at P0.
- `suction_pipe_home()` will move DOWN until P0 is pressed, then stop.

Hardware: tie EN on the driver to GND (or per datasheet).

BCM: STEP=8 (physical pin 24), DIR=20 (physical pin 38).
"""
import RPi.GPIO as GPIO
import time
import smbus

STEP_PIN = 8    # CLK+
DIR_PIN = 20    # CW+

delay = 0.001

_initialized = False
_i2c_initialized = False
_bus = None
PCF8574_ADDRESS = 0x21  # second extender (adjust if your address differs)


def _ensure_gpio():
    global _initialized
    if not _initialized:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(STEP_PIN, GPIO.OUT)
        GPIO.setup(DIR_PIN, GPIO.OUT)
        _initialized = True


def _ensure_i2c():
    """Initialize I2C bus + configure PCF8574 inputs (once)."""
    global _i2c_initialized, _bus
    if not _i2c_initialized:
        _bus = smbus.SMBus(1)
        # Configure all P0–P7 as inputs (write 1s)
        _bus.write_byte(PCF8574_ADDRESS, 0xFF)
        _i2c_initialized = True


def _read_p0():
    """Read PCF8574 P0 state (returns 0 or 1)."""
    _ensure_i2c()
    value = _bus.read_byte(PCF8574_ADDRESS)
    return value & 0x01  # bit0 = P0


def _step(steps, direction_high):
    _ensure_gpio()
    GPIO.output(DIR_PIN, GPIO.HIGH if direction_high else GPIO.LOW)
    for _ in range(steps):
        GPIO.output(STEP_PIN, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(STEP_PIN, GPIO.LOW)
        time.sleep(delay)


def suction_pipe_up(steps):
    """Move suction pipe UP by the given number of steps."""
    print(f"Suction Pipe: moving UP {steps} steps")
    _step(steps, direction_high=False)  # DIR LOW = physical UP


def suction_pipe_down(steps):
    """Move suction pipe DOWN by the given number of steps."""
    print(f"Suction Pipe: moving DOWN {steps} steps")
    _step(steps, direction_high=True)  # DIR HIGH = physical DOWN


def suction_pipe_home():
    """
    Home by moving DOWN until the limit switch on PCF8574 P0 is pressed.

    Assumes typical PCF8574 pull-up behavior:
    - P0 reads 1 when not pressed
    - P0 reads 0 when pressed
    """
    print("Suction Pipe: homing DOWN until P0 limit switch (PCF8574) is pressed")
    _ensure_gpio()
    GPIO.output(DIR_PIN, GPIO.HIGH)  # DIR HIGH = physical DOWN (see suction_pipe_down)

    while True:
        p0 = _read_p0()
        if p0 == 0:
            print("P0 limit switch detected, stopping suction pipe.")
            break

        GPIO.output(STEP_PIN, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(STEP_PIN, GPIO.LOW)
        time.sleep(delay)


# Aliases (optional)
Suction_Pipe_up = suction_pipe_up
Suction_Pipe_down = suction_pipe_down
Suction_Pipe_home = suction_pipe_home


def cleanup():
    """Release state (GPIO cleanup handled by main)."""
    global _initialized, _i2c_initialized, _bus
    if _initialized:
        _initialized = False

    if _i2c_initialized and _bus is not None:
        try:
            _bus.close()
        except AttributeError:
            pass
        _i2c_initialized = False
        _bus = None
