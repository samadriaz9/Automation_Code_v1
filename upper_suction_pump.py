"""
Upper flask DC suction pump (BTS7960 / IBT-2 style — single RPWM PWM line in code).

RPWM pin: GPIO 14 (physical header pin 8).
Use **GPIO 4** for DS18B20 1-Wire temperature sensor (do not share PWM and 1-Wire).

Note: GPIO 14 is UART TX when serial console is enabled; if your BTS7960 input turns on
while the line is HIGH at boot, consider disabling serial console on GPIO 14/15
or add a small boot-time GPIO-safe script for this PWM line.
"""
import RPi.GPIO as GPIO
import time

RPWM_PIN = 14  # BCM — upper suction pump RPWM (physical pin 8)

_pwm_initialized = False
rpwm = None


def _ensure_pwm():
    global _pwm_initialized, rpwm

    if _pwm_initialized:
        return

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(RPWM_PIN, GPIO.OUT)

    rpwm = GPIO.PWM(RPWM_PIN, 1000)
    rpwm.start(0)

    _pwm_initialized = True


def upper_suction_pump_on(speed):
    """Start upper suction pump continuously."""
    _ensure_pwm()

    speed = max(0, min(100, float(speed)))
    print(f"Upper suction pump ON: {speed:.1f}%")

    rpwm.ChangeDutyCycle(speed)


def upper_suction_pump_off():
    """Stop upper suction pump."""
    if _pwm_initialized:
        print("Upper suction pump OFF")
        rpwm.ChangeDutyCycle(0)


def upper_suction_pump(speed, seconds):
    """Run at speed % for seconds (blocking)."""
    upper_suction_pump_on(speed)
    time.sleep(seconds)
    upper_suction_pump_off()


def cleanup():
    """Call once when program exits."""
    global _pwm_initialized, rpwm
    if _pwm_initialized:
        try:
            rpwm.stop()
        except Exception:
            pass
        _pwm_initialized = False


# Backward-compatible aliases (older code may still import these names).
suction_pump_on = upper_suction_pump_on
suction_pump_off = upper_suction_pump_off
suction_pump = upper_suction_pump

