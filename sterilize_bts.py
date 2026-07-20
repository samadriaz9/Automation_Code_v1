"""
Sterilize BTS motor control via the second cascaded PCF8574 I2C expander.

Wiring (second board @ 0x21):
- P2: assembly sterilize BTS
- P3: suction sterilize BTS

Other pins on 0x21 (e.g. P0/P1 limit inputs) are kept HIGH so they stay as inputs.
- P2 (assembly): logic inverter installed — pin LOW = motor ON, pin HIGH = motor OFF
- P3 (suction): logic inverter installed — pin LOW = motor ON, pin HIGH = motor OFF
"""

import time
import smbus

STERILIZE_PCF8574_ADDRESS = 0x21

P2_ASSEMBLY = 2
P3_SUCTION = 3
# Legacy names from earlier wiring revisions (kept for older imports/scripts).
P3_ASSEMBLY = P2_ASSEMBLY
P4_SUCTION = P3_SUCTION

__all__ = [
    "P2_ASSEMBLY",
    "P3_SUCTION",
    "P3_ASSEMBLY",
    "P4_SUCTION",
    "run_sterilize_assembly",
    "run_sterilize_suction",
    "set_sterilize_bts",
    "cleanup",
]
_INVERTED_CHANNELS = {P2_ASSEMBLY, P3_SUCTION}
_BTS_CHANNEL_MASK = (1 << P2_ASSEMBLY) | (1 << P3_SUCTION)
# P2/P3 HIGH (off via inverters), all other pins HIGH
_DEFAULT_STATE = 0xFF

_bus = None
_initialized = False
_state = _DEFAULT_STATE


def _ensure_i2c():
    """Initialize I2C bus for the second PCF8574 (once)."""
    global _bus, _initialized, _state
    if not _initialized:
        _bus = smbus.SMBus(1)
        _state = _DEFAULT_STATE
        _bus.write_byte(STERILIZE_PCF8574_ADDRESS, _state)
        _initialized = True


def _write_state():
    _ensure_i2c()
    _bus.write_byte(STERILIZE_PCF8574_ADDRESS, _state)


def set_sterilize_bts(channel: int, on: bool):
    """
    Turn a sterilize BTS channel ON or OFF.

    channel: P2_ASSEMBLY (2) or P3_SUCTION (3)
    on=True  -> BTS ON
    on=False -> BTS OFF
    """
    global _state
    if channel not in (P2_ASSEMBLY, P3_SUCTION):
        raise ValueError(f"channel must be P2_ASSEMBLY ({P2_ASSEMBLY}) or P3_SUCTION ({P3_SUCTION})")

    mask = 1 << channel
    inverted = channel in _INVERTED_CHANNELS
    if on:
        if inverted:
            _state &= ~mask  # LOW through inverter -> motor ON
        else:
            _state |= mask   # HIGH -> motor ON
    else:
        if inverted:
            _state |= mask   # HIGH through inverter -> motor OFF
        else:
            _state &= ~mask  # LOW -> motor OFF
    _write_state()


def run_sterilize_assembly(seconds: float = 5.0):
    """Run assembly sterilize BTS for the given duration (blocking)."""
    if seconds < 0:
        raise ValueError("seconds must be >= 0")

    _ensure_i2c()
    print(f"Sterilize_Assembly: BTS ON for {seconds}s (PCF8574 P2)")
    set_sterilize_bts(P2_ASSEMBLY, True)
    time.sleep(seconds)
    print("Sterilize_Assembly: BTS OFF")
    set_sterilize_bts(P2_ASSEMBLY, False)


def run_sterilize_suction(seconds: float = 5.0):
    """Run suction sterilize BTS for the given duration (blocking)."""
    if seconds < 0:
        raise ValueError("seconds must be >= 0")

    _ensure_i2c()
    print(f"Sterilize_Suction: BTS ON for {seconds}s (PCF8574 P3)")
    set_sterilize_bts(P3_SUCTION, True)
    time.sleep(seconds)
    print("Sterilize_Suction: BTS OFF")
    set_sterilize_bts(P3_SUCTION, False)


def cleanup():
    """Turn both sterilize BTS channels off and close the I2C bus."""
    global _bus, _initialized, _state
    if _initialized and _bus is not None:
        try:
            _state = _DEFAULT_STATE
            _bus.write_byte(STERILIZE_PCF8574_ADDRESS, _state)
        except Exception:
            pass
        try:
            _bus.close()
        except AttributeError:
            pass
    _bus = None
    _initialized = False
