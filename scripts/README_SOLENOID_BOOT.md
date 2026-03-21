# Solenoid turns ON when Raspberry Pi boots (without running `main.py`)

## Why this happens

- **GPIO 14 (BCM)** is **UART TX** on the 40-pin header. While the serial console is enabled, this line is often **HIGH** during/after boot.
- If your relay/driver is **active HIGH** (GPIO HIGH = valve ON), that idle HIGH can **energize the solenoid** before your Python code runs.

## Fix A — Software (recommended first)

1. Copy the boot script and service to the Pi (paths are relative to the repo root):

   ```bash
   sudo cp scripts/solenoid_boot_safe.sh /usr/local/bin/
   sudo chmod +x /usr/local/bin/solenoid_boot_safe.sh
   sudo cp scripts/solenoid-gpio-boot.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable solenoid-gpio-boot.service
   sudo systemctl start solenoid-gpio-boot.service
   ```

2. Reboot and check the valve stays off until you run your program.

If you change the pin in `solinoid_value.py`, set the same number when installing:

```bash
export SOLENOID_BOOT_PIN=17   # example
sudo -E env SOLENOID_BOOT_PIN=$SOLENOID_BOOT_PIN /usr/local/bin/solenoid_boot_safe.sh
```

Edit the service file or add `Environment=SOLENOID_BOOT_PIN=17` under `[Service]`.

## Fix B — Hardware / wiring (best long-term)

- Move the solenoid control to a **GPIO that is not UART** (e.g. **GPIO 17, 22, 27** BCM) and update `SOLENOID_PIN` in `solinoid_value.py`.
- Or add a **pull-down** on the control line so an undriven pin defaults to OFF (depends on your relay module logic).

## Fix C — Disable serial on GPIO 14/15 (optional)

If you don’t need serial console on the UART pins, you can disable it in `raspi-config` → Interface Options → Serial → login shell off. This reduces stray activity on GPIO 14 but **Fix A or B** is still more reliable.

## Inverted relay (active LOW)

If your module turns ON when GPIO is **LOW**, say so in your project notes; boot behaviour is the opposite and you’d use `raspi-gpio` to drive **high** for OFF instead (hardware-dependent).
