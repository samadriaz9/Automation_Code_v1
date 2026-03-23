# Drain Solenoid Boot-Safe

Your drain solenoid is controlled by `solinoid_value_drain.py` on **GPIO 9** (pin 21).

The drain boot-safe service forces GPIO 9 to **LOW** at boot, so an active-HIGH solenoid/driver stays OFF.

## Install (once on the Pi)

```bash
# Reuse the repo boot script already used for the filtration solenoid:
sudo cp scripts/solenoid_boot_safe.sh /usr/local/bin/
sudo chmod +x /usr/local/bin/solenoid_boot_safe.sh

# Install drain service:
sudo cp scripts/solenoid_drain-gpio-boot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable solenoid_drain-gpio-boot.service
sudo systemctl start solenoid_drain-gpio-boot.service
```

