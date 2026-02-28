import RPi.GPIO as GPIO
import time

# ---------- PIN SETUP (BCM numbers!) ----------
RPWM_PIN = 4   # physical pin 32
#LPWM_PIN = 19   # physical pin 35
#LPWM_PIN = 11
#EN_PIN   = 12    # physical pin 7

GPIO.setmode(GPIO.BCM)

GPIO.setup(RPWM_PIN, GPIO.OUT)
#GPIO.setup(LPWM_PIN, GPIO.OUT)
#GPIO.setup(EN_PIN, GPIO.OUT)

#GPIO.output(EN_PIN, GPIO.HIGH)  # Enable BTS module

rpwm = GPIO.PWM(RPWM_PIN, 1000)
#lpwm = GPIO.PWM(LPWM_PIN, 1000)

rpwm.start(0)
#lpwm.start(0)

# ---------- FUNCTIONS ----------
def low_speed():
    print("LOW speed (Filter paper)")
    rpwm.ChangeDutyCycle(40)
 #   lpwm.ChangeDutyCycle(0)

def high_speed():
    print("HIGH speed (Petri dish)")
    rpwm.ChangeDutyCycle(80)
  #  lpwm.ChangeDutyCycle(0)

def stop_motor():
    print("Motor stopped")
    rpwm.ChangeDutyCycle(0)
   # lpwm.ChangeDutyCycle(0)

# ---------- MAIN LOOP ----------
try:
    while True:
        print("\n===== AIR PUMP MENU =====")
        print("1. LOW speed (Filter paper)")
        print("2. HIGH speed (Petri dish)")
        print("3. Stop")
        print("4. Exit")

        choice = input("Select option: ")

        if choice == "1":
            low_speed()
        elif choice == "2":
            high_speed()
        elif choice == "3":
            stop_motor()
        elif choice == "4":
            break
        else:
            print("Invalid choice")

except KeyboardInterrupt:
    pass

finally:
    stop_motor()
    rpwm.stop()
   # lpwm.stop()
    GPIO.cleanup()