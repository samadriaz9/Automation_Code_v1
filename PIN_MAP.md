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
| **camera_module** | 5 STEP, 7 DIR, **9 EN** | If USB camera path is used, GPIO 9 can be reassigned |
| **media_dispensor** | 24 STEP, 27 DIR | EN tied on driver; physical pins 18 & 13 |
| **suction_pipe** | 8 STEP, 20 DIR | EN tied on driver; **no** limit switch (up/down by steps only) |
| **incubator_lid** | 6 STEP, 16 DIR | EN tied on driver; **no** limit; physical pins 31 & 36 |
| **upper_suction_pump** (upper DC BTS) | **11** RPWM | Pin 23; **GPIO 4 free** for DS18B20; SPI off → GPIO 11 OK |
| **filteration_suction_pump** (DC PWM) | **25** | |
| **solinoid_value_to_filteration** | **26** | Filtration solenoid; pin 37; avoids UART TX (see `solinoid_value_to_filteration.py`) |
| **solinoid_value_drain** | **9** | Drain solenoid; pin 21; boot-safe service available |
| **solinoid_waste** | **0** | Waste solenoid; pin 27; HAT EEPROM disabled required |
| **water_level_sensor** | **1** (input) | Pin 28; read by `solinoid_value_to_filteration.py` |
| **relay_control** | *none* | I2C address **0x21** |

**PCF8574 @ 0x20 — limit inputs (shared bus):** P0 filtration flask, P2 suction lift, P3 camera, **P4 petri_dishes**, **P5 media_dispensor**, P6 filtration unit. (P1/P7 free if you add more limits.)

**DS18B20 temperature sensor:** use **GPIO 4** (pin 7) with `dtoverlay=w1-gpio` — do **not** use GPIO 4 for anything else (upper DC pump moved to GPIO 11).

## Pins often still free on a Pi 3/4/5 (check your wiring)

After upper_suction_pump on **GPIO 11**, typical remaining: **26** (and more). Use these first before reusing anything.

## If you run out of pins

1. **Tie EN on the driver** (no GPIO) — same as most of your steppers; **camera_module** can be changed the same way to free **GPIO 9**.
2. **Do not share** one GPIO between DS18B20 (1-Wire) and BTS7960 PWM — use separate pins; keep **GPIO 4** for temp **or** for BTS, not both.
3. **Solenoid via relay** — drive a relay channel on your PCF8574 relay board instead of a direct GPIO (saves one pin if timing is OK).
4. **I2C GPIO expander** (MCP23017, extra PCF8574) — good for **slow** outputs (LEDs, solenoid via transistor); **not** for stepper STEP/DIR (too slow).
5. **Pi Zero** — fewer header pins; same ideas, tighter map.

## Quick wins

| Change | Frees |
|--------|--------|
| consumable: EN tied on hardware (done in code) | **GPIO 14** freed (no longer used by upper_suction_pump PWM) |
| camera: EN tied on hardware (if you update `camera_module.py` like other steppers) | **GPIO 9** (used by drain solenoid now) |
