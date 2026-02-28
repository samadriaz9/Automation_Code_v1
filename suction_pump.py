import RPi.GPIO as GPIO
import time

# ---------- PIN SETUP ----------
RPWM_PIN = 4   # BCM

_pwm_initialized = False
rpwm = None


def _ensure_pwm():
    """Initialize PWM once."""
    global _pwm_initialized, rpwm

    if _pwm_initialized:
        return

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(RPWM_PIN, GPIO.OUT)

    rpwm = GPIO.PWM(RPWM_PIN, 1000)
    rpwm.start(0)

    _pwm_initialized = True


# ✅ NEW — continuous ON
def suction_pump_on(speed):
    """Start suction pump continuously."""
    _ensure_pwm()

    speed = max(0, min(100, float(speed)))
    print(f"Suction pump ON: {speed:.1f}%")

    rpwm.ChangeDutyCycle(speed)


# ✅ NEW — stop
def suction_pump_off():
    """Stop suction pump."""
    if _pwm_initialized:
        print("Suction pump OFF")
        rpwm.ChangeDutyCycle(0)


# ✅ OLD — keep for compatibility
def suction_pump(speed, seconds):
    """
    Run suction pump at given speed for given seconds.
    (Blocking version)
    """
    suction_pump_on(speed)
    time.sleep(seconds)
    suction_pump_off()


def cleanup():
    """Call once when program exits."""
    global _pwm_initialized, rpwm
    if _pwm_initialized:
        try:
            rpwm.stop()
        except:
            pass
        _pwm_initialized = False