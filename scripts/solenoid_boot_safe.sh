#!/bin/bash
# Run at boot to keep the solenoid GPIO in a safe OFF state before your app runs.
# GPIO 14 is UART TX — without this, the pin can sit HIGH at boot and turn the valve ON.
#
# Install (once on the Pi):
#   sudo cp scripts/solenoid_boot_safe.sh /usr/local/bin/
#   sudo chmod +x /usr/local/bin/solenoid_boot_safe.sh
#   sudo cp scripts/solenoid-gpio-boot.service /etc/systemd/system/
#   sudo systemctl enable solenoid-gpio-boot.service
#   sudo systemctl start solenoid-gpio-boot.service
#
# Must match SOLENOID_PIN in solinoid_value.py
PIN="${SOLENOID_BOOT_PIN:-14}"

if command -v raspi-gpio >/dev/null 2>&1; then
  # Output, drive low (valve OFF if your driver is active-HIGH)
  raspi-gpio set "$PIN" op dl
  exit 0
fi

echo "solenoid_boot_safe.sh: raspi-gpio not found; install raspi-utils or use Bookworm/Trixie Raspberry Pi OS" >&2
exit 1
