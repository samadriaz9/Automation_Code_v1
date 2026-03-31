"""
Incubator lid stepper control.

- STEP uses direct GPIO: STEP=6 (physical pin 31)
- DIR (CW+) uses second I2C expander PCF8574: address 0x21, pin P1
- No limit switch logic in this module

Hardware: tie EN on the driver to GND (or per datasheet).
"""
import RPi.GPIO as GPIO
import time
import smbus

STEP_PIN = 6    # CLK+

delay = 0.001

_initialized = False
_i2c_initialized = False
_bus = None
_pcf_state = 0xFF

# Second I2C expander used for DIR (CW+) output.
PCF8574_ADDRESS = 0x21
DIR_P = 1  # use P1 as CW+/DIR signal


def _ensure_gpio():
    global _initialized
    if not _initialized:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(STEP_PIN, GPIO.OUT, initial=GPIO.LOW)
        _initialized = True


def _ensure_i2c():
    """Initialize I2C bus + keep current PCF8574 state (once)."""
    global _i2c_initialized, _bus, _pcf_state
    if not _i2c_initialized:
        _bus = smbus.SMBus(1)
        try:
            _pcf_state = _bus.read_byte(PCF8574_ADDRESS)
        except Exception:
            _pcf_state = 0xFF
            _bus.write_byte(PCF8574_ADDRESS, _pcf_state)
        _i2c_initialized = True


def _set_dir(direction_high: bool):
    """Drive PCF8574 P1 as DIR/CW+ output."""
    _ensure_i2c()
    global _pcf_state
    mask = 1 << DIR_P
    if direction_high:
        _pcf_state |= mask
    else:
        _pcf_state &= ~mask
    _bus.write_byte(PCF8574_ADDRESS, _pcf_state)


def _step(steps, direction_high):
    _ensure_gpio()
    _set_dir(direction_high)
    # Some stepper drivers need a short DIR setup time before the first step edge.
    time.sleep(delay)
    for _ in range(steps):
        GPIO.output(STEP_PIN, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(STEP_PIN, GPIO.LOW)
        time.sleep(delay)


def incubator_lid_up(steps):
    """Move incubator lid UP by the given number of steps."""
    print(f"Incubator lid: moving UP {steps} steps (DIR=P1 HIGH)")
    _step(steps, direction_high=True)


def incubator_lid_down(steps):
    """Move incubator lid DOWN by the given number of steps."""
    print(f"Incubator lid: moving DOWN {steps} steps (DIR=P1 LOW)")
    _step(steps, direction_high=False)


def incubator_lid_home():
    """No limit switch — no homing."""
    print("Incubator lid: no limit switch configured — incubator_lid_home() skipped.")


# Optional CamelCase aliases
Incubator_lid_up = incubator_lid_up
Incubator_lid_down = incubator_lid_down
Incubator_lid_home = incubator_lid_home


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
