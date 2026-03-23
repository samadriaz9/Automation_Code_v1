#!/bin/bash
# Run at boot to keep the upper pump PWM GPIO in a safe OFF state before your app runs.
#
# Default OFF pin (GPIO 11 / physical pin 23) must match UPPER_PUMP_PIN in upper_suction_pump.py.
#
# Install (once on the Pi):
#   sudo cp scripts/upper_pump_boot_safe.sh /usr/local/bin/
#   sudo chmod +x /usr/local/bin/upper_pump_boot_safe.sh
#   sudo cp scripts/upper-pump-gpio-boot.service /etc/systemd/system/
#   sudo systemctl daemon-reload
#   sudo systemctl enable upper-pump-gpio-boot.service
#   sudo systemctl start upper-pump-gpio-boot.service

PIN="${UPPER_PUMP_BOOT_PIN:-11}"

if command -v raspi-gpio >/dev/null 2>&1; then
  # Output, drive low (OFF if your BTS7960 input is active-HIGH)
  raspi-gpio set "$PIN" op dl
  exit 0
fi

echo "upper_pump_boot_safe.sh: raspi-gpio not found; install raspi-utils or use Bookworm/Trixie Raspberry Pi OS" >&2
exit 1

