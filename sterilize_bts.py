"""
Sterilize BTS motor control via the second cascaded PCF8574 I2C expander.

Wiring (second board @ 0x21):
- P3: assembly sterilize BTS
- P4: suction sterilize BTS

Other pins on 0x21 (e.g. P0/P1 limit inputs) are kept HIGH so they stay as inputs.
PCF8574 outputs are active-low: bit 0 = ON, bit 1 = OFF.
"""

import time
import smbus

STERILIZE_PCF8574_ADDRESS = 0x21

P3_ASSEMBLY = 3
P4_SUCTION = 4

_bus = None
_initialized = False
_state = 0xFF


def _ensure_i2c():
    """Initialize I2C bus for the second PCF8574 (once)."""
    global _bus, _initialized, _state
    if not _initialized:
        _bus = smbus.SMBus(1)
        _state = 0xFF
        _bus.write_byte(STERILIZE_PCF8574_ADDRESS, _state)
        _initialized = True


def _write_state():
    _ensure_i2c()
    _bus.write_byte(STERILIZE_PCF8574_ADDRESS, _state)


def set_sterilize_bts(channel: int, on: bool):
    """
    Turn a sterilize BTS channel ON or OFF.

    channel: P3_ASSEMBLY (3) or P4_SUCTION (4)
    on=True  -> BTS ON  (pin driven LOW)
    on=False -> BTS OFF (pin driven HIGH)
    """
    global _state
    if channel not in (P3_ASSEMBLY, P4_SUCTION):
        raise ValueError(f"channel must be P3_ASSEMBLY ({P3_ASSEMBLY}) or P4_SUCTION ({P4_SUCTION})")

    mask = 1 << channel
    if on:
        _state &= ~mask
    else:
        _state |= mask
    _write_state()


def run_sterilize_assembly(seconds: float = 5.0):
    """Run assembly sterilize BTS for the given duration (blocking)."""
    if seconds < 0:
        raise ValueError("seconds must be >= 0")

    _ensure_i2c()
    print(f"Sterilize_Assembly: BTS ON for {seconds}s (PCF8574 P3)")
    set_sterilize_bts(P3_ASSEMBLY, True)
    time.sleep(seconds)
    print("Sterilize_Assembly: BTS OFF")
    set_sterilize_bts(P3_ASSEMBLY, False)


def run_sterilize_suction(seconds: float = 5.0):
    """Run suction sterilize BTS for the given duration (blocking)."""
    if seconds < 0:
        raise ValueError("seconds must be >= 0")

    _ensure_i2c()
    print(f"Sterilize_Suction: BTS ON for {seconds}s (PCF8574 P4)")
    set_sterilize_bts(P4_SUCTION, True)
    time.sleep(seconds)
    print("Sterilize_Suction: BTS OFF")
    set_sterilize_bts(P4_SUCTION, False)


def cleanup():
    """Turn both sterilize BTS channels off and close the I2C bus."""
    global _bus, _initialized, _state
    if _initialized and _bus is not None:
        try:
            _state = 0xFF
            _bus.write_byte(STERILIZE_PCF8574_ADDRESS, _state)
        except Exception:
            pass
        try:
            _bus.close()
        except AttributeError:
            pass
    _bus = None
    _initialized = False
