import RPi.GPIO as GPIO
import time

# --- DC suction pump via IBT-2 (BTS7960) ---
# Wiring (BCM numbering):
#   RPWM -> GPIO 4
#   LPWM -> GPIO 11
#   VCC  -> 5V
#   REN/LEN -> tied to VCC (always enabled)

RPWM_PIN = 4
LPWM_PIN = 11

PWM_FREQUENCY = 1000  # Hz

_pwm_initialized = False
_pwm_r = None
_pwm_l = None


def _ensure_pwm():
    """Initialize PWM outputs for the DC suction pump (once)."""
    global _pwm_initialized, _pwm_r, _pwm_l
    if not _pwm_initialized:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(RPWM_PIN, GPIO.OUT)
        GPIO.setup(LPWM_PIN, GPIO.OUT)

        _pwm_r = GPIO.PWM(RPWM_PIN, PWM_FREQUENCY)
        _pwm_l = GPIO.PWM(LPWM_PIN, PWM_FREQUENCY)

        _pwm_r.start(0)
        _pwm_l.start(0)

        _pwm_initialized = True


def suction_pump(speed_percent: float, seconds: float):
    """
    Run the DC suction pump at a given speed (0–100 %) for `seconds` seconds.

    Example:
        suction_pump(100, 2)  # 100% power for 2 seconds
        suction_pump(50, 2)   # 50% power for 2 seconds
    """
    _ensure_pwm()

    # Clamp values to safe ranges
    speed = max(0.0, min(100.0, float(speed_percent)))
    duration = max(0.0, float(seconds))

    print(f"Suction pump DC: {speed:.1f}% for {duration:.2f}s")

    # One direction only: RPWM = PWM, LPWM = 0
    _pwm_r.ChangeDutyCycle(speed)
    _pwm_l.ChangeDutyCycle(0.0)

    time.sleep(duration)

    # Stop pump
    _pwm_r.ChangeDutyCycle(0.0)
    _pwm_l.ChangeDutyCycle(0.0)


def cleanup():
    """Stop PWM and release GPIO for the suction pump."""
    global _pwm_initialized, _pwm_r, _pwm_l
    if _pwm_initialized:
        try:
            _pwm_r.stop()
            _pwm_l.stop()
        except Exception:
            pass
        _pwm_initialized = False
    # Do NOT call GPIO.cleanup() here; main.py handles global cleanup.

