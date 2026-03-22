"""
Flask DC suction pump (BTS7960 / IBT-2 style — single RPWM PWM line in code).

**GPIO 4 is NOT used** so you can use **GPIO 4** for a DS18B20 1-Wire temperature sensor
(default `w1-gpio` on many Pi images). Do not connect both pump PWM and 1-Wire to the same pin.

**RPWM** default: **GPIO 11** (physical pin 23). With **SPI disabled** (raspi-config), GPIO 11 is free for PWM.

LPWM / REN / LEN: wire per your BTS7960 board (same idea as other DC motor modules).
"""
import RPi.GPIO as GPIO
import time

RPWM_PIN = 11  # BCM — keep GPIO 4 free for DS18B20 1-Wire

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


def suction_pump_on(speed):
    """Start suction pump continuously."""
    _ensure_pwm()

    speed = max(0, min(100, float(speed)))
    print(f"Suction pump ON: {speed:.1f}%")

    rpwm.ChangeDutyCycle(speed)


def suction_pump_off():
    """Stop suction pump."""
    if _pwm_initialized:
        print("Suction pump OFF")
        rpwm.ChangeDutyCycle(0)


def suction_pump(speed, seconds):
    """Run at speed % for seconds (blocking)."""
    suction_pump_on(speed)
    time.sleep(seconds)
    suction_pump_off()


def cleanup():
    global _pwm_initialized, rpwm
    if _pwm_initialized:
        try:
            rpwm.stop()
        except Exception:
            pass
        _pwm_initialized = False
