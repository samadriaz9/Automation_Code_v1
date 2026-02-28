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


def suction_pump(speed, seconds):
    """
    Run suction pump at given speed (0–100) for given seconds.
    Example:
        suction_pump(80, 3)
    """
    _ensure_pwm()

    # clamp values safely
    speed = max(0, min(100, float(speed)))
    seconds = max(0, float(seconds))

    print(f"Suction pump: {speed:.1f}% for {seconds:.2f}s")

    rpwm.ChangeDutyCycle(speed)
    time.sleep(seconds)
    rpwm.ChangeDutyCycle(0)


def cleanup():
    """Call once when program exits."""
    global _pwm_initialized, rpwm
    if _pwm_initialized:
        try:
            rpwm.stop()
        except:
            pass
        _pwm_initialized = False
    # GPIO.cleanup() should be called by main program