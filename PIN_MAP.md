# GPIO allocation (BCM numbering)

Use this to spot conflicts and free pins. **I2C** uses GPIO **2 & 3** (SDA/SCL) for PCF8574 expanders — keep those free for wiring.

## Current modules (automation stack)

| Module | Pins (BCM) | Notes |
|--------|----------------|-------|
| **filteration_flask** | 18 STEP, 23 DIR | EN tied on driver |
| **filteration_unit** | 13 STEP, 19 DIR | EN tied on driver |
| **suction_pump_up_down** (stepper lift) | 21 STEP, 12 DIR | EN tied on driver |
| **consumable** | 17 STEP, 15 DIR | EN tied on driver (GPIO 14 freed) |
| **petri_dishes** | 10 STEP, 22 DIR | EN tied on driver |
| **camera_module** | 5 STEP, 7 DIR, **9 EN** | Only module still using **EN** in software |
| **media_dispensor** | 24 STEP, 27 DIR | EN tied on driver; physical pins 18 & 13 |
| **suction_pipe** | 8 STEP, 20 DIR | EN tied on driver; **no** limit switch (up/down by steps only) |
| **suction_pump** (DC BTS) | **4** RPWM (single direction in code) | Add LPWM in code if you use reverse |
| **filteration_suction_pump** (DC PWM) | **25** | |
| **solinoid_value** | **14** | UART TX — use boot script or move pin (see `solinoid_value.py`) |
| **relay_control** | *none* | I2C address **0x21** |

**PCF8574 @ 0x20 — limit inputs (shared bus):** P0 filtration flask, P2 suction lift, P3 camera, **P4 petri_dishes**, **P5 media_dispensor**, P6 filtration unit. (P1/P7 free if you add more limits.)

## Pins often still free on a Pi 3/4/5 (check your wiring)

Typical unused if you only use the table above: **6, 8, 11, 16, 20, 26** (and more). Use these first before reusing anything.

## If you run out of pins

1. **Tie EN on the driver** (no GPIO) — same as most of your steppers; **camera_module** can be changed the same way to free **GPIO 9**.
2. **Do not share** one GPIO between DS18B20 (1-Wire) and BTS7960 PWM — use separate pins; keep **GPIO 4** for temp **or** for BTS, not both.
3. **Solenoid via relay** — drive a relay channel on your PCF8574 relay board instead of a direct GPIO (saves one pin if timing is OK).
4. **I2C GPIO expander** (MCP23017, extra PCF8574) — good for **slow** outputs (LEDs, solenoid via transistor); **not** for stepper STEP/DIR (too slow).
5. **Pi Zero** — fewer header pins; same ideas, tighter map.

## Quick wins

| Change | Frees |
|--------|--------|
| consumable: EN tied on hardware (done in code) | **GPIO 14** → solenoid only (no clash with consumable) |
| camera: EN tied on hardware (if you update `camera_module.py` like other steppers) | **GPIO 9** |
