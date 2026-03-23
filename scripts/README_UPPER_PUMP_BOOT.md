# Upper Pump Boot-Safe

Your upper suction pump is driven by **GPIO 11 (RPWM)**.
GPIO 11 is a non-UART pin and typically does not glitch HIGH during boot.

This script forces **GPIO 11 LOW** at boot so the BTS7960 input stays OFF until your program starts.

## Install

On the Raspberry Pi:

```bash
sudo cp scripts/upper_pump_boot_safe.sh /usr/local/bin/
sudo chmod +x /usr/local/bin/upper_pump_boot_safe.sh

sudo cp scripts/upper-pump-gpio-boot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable upper-pump-gpio-boot.service
sudo systemctl start upper-pump-gpio-boot.service
```

## If the pump still turns on

Your BTS7960 board / wiring may be **active LOW** (OFF when GPIO is HIGH).
In that case, tell me and I’ll provide the inverted boot-safe line.

