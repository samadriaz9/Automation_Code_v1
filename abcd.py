import RPi.GPIO as GPIO
import time

RPWM = 4
LPWM = 18
REN = 5
LEN = 6

GPIO.setmode(GPIO.BCM)

GPIO.setup(RPWM, GPIO.OUT)
GPIO.setup(LPWM, GPIO.OUT)
GPIO.setup(REN, GPIO.OUT)
GPIO.setup(LEN, GPIO.OUT)

GPIO.output(REN, GPIO.HIGH)
GPIO.output(LEN, GPIO.HIGH)

pwm_r = GPIO.PWM(RPWM, 500)
pwm_l = GPIO.PWM(LPWM, 500)

pwm_r.start(70)
pwm_l.start(0)

time.sleep(5)

pwm_r.stop()
pwm_l.stop()
GPIO.cleanup()