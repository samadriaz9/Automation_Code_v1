import RPi.GPIO as GPIO
import time

# ---------- PIN SETUP (BCM numbers!) ----------
RPWM_PIN = 12   # PWM here
LPWM_PIN = 19   # MUST stay digital LOW

GPIO.setmode(GPIO.BCM)

GPIO.setup(RPWM_PIN, GPIO.OUT)
GPIO.setup(LPWM_PIN, GPIO.OUT)

# Force reverse side OFF
GPIO.output(LPWM_PIN, GPIO.LOW)

rpwm = GPIO.PWM(RPWM_PIN, 1000)
rpwm.start(0)

# ---------- FUNCTIONS ----------
def low_speed():
    print("LOW speed (Filter paper)")
    GPIO.output(LPWM_PIN, GPIO.LOW)  # keep LOW
    rpwm.ChangeDutyCycle(40)

def high_speed():
    print("HIGH speed (Petri dish)")
    GPIO.output(LPWM_PIN, GPIO.LOW)  # keep LOW
    rpwm.ChangeDutyCycle(80)

def stop_motor():
    print("Motor stopped")
    rpwm.ChangeDutyCycle(0)
    GPIO.output(LPWM_PIN, GPIO.LOW)
    
    
low_speed()