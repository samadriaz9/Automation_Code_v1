import glob
import time

from relay_control import P1, set_relay


def _read_ds18b20_c(sensor_glob="/sys/bus/w1/devices/28-*/w1_slave"):
    """
    Read DS18B20 temperature in Celsius from w1 sysfs.
    Raises RuntimeError if sensor file is missing or CRC/data invalid.
    """
    paths = glob.glob(sensor_glob)
    if not paths:
        raise RuntimeError("DS18B20 not found under /sys/bus/w1/devices/28-*/w1_slave")

    with open(paths[0], "r", encoding="utf-8") as f:
        lines = f.read().strip().splitlines()

    if len(lines) < 2 or not lines[0].strip().endswith("YES"):
        raise RuntimeError("DS18B20 CRC invalid (first line does not end with YES)")

    marker = "t="
    if marker not in lines[1]:
        raise RuntimeError("DS18B20 temperature token 't=' not found")

    milli_c = int(lines[1].split(marker, 1)[1])
    return milli_c / 1000.0


def Start_incubation(target_temp_c, duration_minutes, hysteresis_c=0.3, poll_seconds=2.0):
    """
    Maintain incubation temperature using heater relay on P1.

    Args:
        target_temp_c: target temperature in Celsius.
        duration_minutes: how long to maintain incubation.
        hysteresis_c: deadband to prevent relay chatter.
        poll_seconds: sensor polling interval.
    """
    target_temp_c = float(target_temp_c)
    duration_s = max(0.0, float(duration_minutes) * 60.0)
    hysteresis_c = max(0.05, float(hysteresis_c))
    poll_seconds = max(0.2, float(poll_seconds))

    lower = target_temp_c - hysteresis_c
    upper = target_temp_c + hysteresis_c

    print(
        f"[Incubation] Start: target={target_temp_c:.2f}C, "
        f"duration={duration_minutes} min, band=({lower:.2f}..{upper:.2f})"
    )

    heater_on = False
    start = time.time()

    try:
        while (time.time() - start) < duration_s:
            temp_c = _read_ds18b20_c()

            if temp_c <= lower and not heater_on:
                set_relay(P1, True)  # ON (active-low relay board handled in relay_control)
                heater_on = True
                print(f"[Incubation] {temp_c:.2f}C -> heater ON")
            elif temp_c >= upper and heater_on:
                set_relay(P1, False)
                heater_on = False
                print(f"[Incubation] {temp_c:.2f}C -> heater OFF")
            else:
                state = "ON" if heater_on else "OFF"
                print(f"[Incubation] {temp_c:.2f}C -> heater {state}")

            time.sleep(poll_seconds)
    finally:
        # Safety: always leave heater OFF on function exit.
        try:
            set_relay(P1, False)
        except Exception:
            pass
        print("[Incubation] Completed. Heater OFF.")

