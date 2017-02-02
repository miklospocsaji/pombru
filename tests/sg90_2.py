import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.OUT)

try:
    while True:
        GPIO.output(18, 1)
        time.sleep(0.0006)
        GPIO.output(18, 0)
        time.sleep(1)
finally:
    GPIO.cleanup()
