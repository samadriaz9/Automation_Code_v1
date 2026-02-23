import RPi.GPIO as GPIO
import time

#  MOTOR PINS

STEP_PIN = 18  # CLK+
DIR_PIN = 23  # CW+
EN_PIN = 24  # EN+

#       LIMIT SWITCH  PINS

LEFT_LIMIT = 17 #  Suction 
RIGHT_LIMIT = 27  #  Filtration

#      GPIO SETUP
GPIO.setmode(GPIO.BCM)

GPIO.setup(STEP_PIN, GPIO.OUT)
GPIO.setup(DIR_PIN, GPIO.OUT)
GPIO.setup(EN_PIN, GPIO.OUT)

GPIO.setup(LEFT_LIMIT, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(RIGHT_LIMIT, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Enable motor (LOW = enable)
GPIO.output(EN_PIN, GPIO.LOW)

#  steps = 1000     #  number of steps
delay = 0.001   # speed control

def move_left():
    print("\nSuction selected Moving LEFT")
    GPIO.output(DIR_PIN, GPIO.HIGH)

    while GPIO.input(LEFT_LIMIT) == GPIO.HIGH:
        GPIO.output(STEP_PIN, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(STEP_PIN, GPIO.LOW)
        time.sleep(delay)

    print("LEFT limit switch pressed Motor stopped")

def move_right():
    print("\nFiltration selected Moving RIGHT")
    GPIO.output(DIR_PIN, GPIO.LOW)

    while GPIO.input(RIGHT_LIMIT) == GPIO.HIGH:
        GPIO.output(STEP_PIN, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(STEP_PIN, GPIO.LOW)
        time.sleep(delay)

    print("RIGHT limit switch pressed Motor stopped")

try:
    while True:
        print("\n========== MENU ==========")
        print("1. Suction (LEFT)")
        print("2. Filtration (RIGHT)")
        print("3. Exit")
        choice = input("Select option: ")

        if choice == "1":
            move_left()
        elif choice == "2":
            move_right()
        elif choice == "3":
            print("Exiting program")
            break
        else:
            print("Invalid choice, try again")

except KeyboardInterrupt:
    print("\nStopped by user")

finally:
    GPIO.output(EN_PIN, GPIO.HIGH)
    GPIO.cleanup()
