import RPi.GPIO as GPIO
import time

# ---------- PIN SETUP ----------
RPWM_PIN = 25  # BCM (NEW PIN)

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


# ? continuous ON
def filteration_suction_pump_on(speed):
    """Start filtration suction pump continuously."""
    _ensure_pwm()

    speed = max(0, min(100, float(speed)))
    print(f"Filteration suction pump ON: {speed:.1f}%")

    rpwm.ChangeDutyCycle(speed)


# ? stop
def filteration_suction_pump_off():
    """Stop filtration suction pump."""
    if _pwm_initialized:
        print("Filteration suction pump OFF")
        rpwm.ChangeDutyCycle(0)


# ? blocking version (optional compatibility)
def filteration_suction_pump(speed, seconds):
    """
    Run filtration suction pump at given speed for given seconds.
    """
    filteration_suction_pump_on(speed)
    time.sleep(seconds)
    filteration_suction_pump_off()


def cleanup():
    """Call once when program exits."""
    global _pwm_initialized, rpwm
    if _pwm_initialized:
        try:
            rpwm.stop()
        except:
            pass
        _pwm_initialized = False