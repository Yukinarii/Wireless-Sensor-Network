import threading
import RPi.GPIO as GPIO
import time

SERVO_PIN = 20
PWM_FREQ = 50
STEP = 18
BUZZER_PIN = 4
BUTTON_PIN = 21
LED1_PIN = 2
LED2_PIN = 3
STATE_ALERT = 1
STATE_NORMAL = 0
STATE = 0


class traffic_system:
    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down = GPIO.PUD_UP)
        GPIO.setup(LED1_PIN, GPIO.OUT)
        GPIO.setup(LED2_PIN, GPIO.OUT)
        GPIO.setup(BUZZER_PIN, GPIO.OUT)
        pwm = GPIO.PWM(SERVO_PIN, GPIO.OUT)
        pwm.start(0)
        GPIO.add_event_detect(BUTTON_PIN, GPIO.FALLING, callback = _button_callback, bouncetime = 250)

    def _button_callback(self):
        STATE = STATE_ALERT
    
    def _buzzer(self):
        while True:
            if STATE is STATE_ALERT:
                GPIO.output(BUZZER_PIN, GPIO.HIGH)
                sleep(0.1)
                GPIO.output(BUZZER_PIN, GPIO.LOW)
                sleep(0.1)
            else:
                GPIO.output(BUZZER_PIN, GPIO.LOW)

    def _servo(self):
        while True:
            if STATE is STATE_ALERT:
                for angle in range(0, 90, STEP):
                    dc = angle_to_duty_cycle(angle)
                    pwm.ChangeDutyCycle(dc)
                    time.sleep(1)
                while True:
                    next
            else:
                for angle in range(90, 0, -STEP):
                    dc = angle_to_duty_cycle(angle)
                    pwm.ChangeDutyCycle(dc)
                    time.sleep(1)
                while True:
                    next

    def angle_to_duty_cycle(angle = 0):
        duty_cycle = (0.05 * PWM_FREQ) + (0.19 * PWM_FREQ * angle / 180)
        return duty_cycle

    def light_blink(self, gpio_num, mutex):
        while True:
            if STATE is STATE_ALERT:
                mutex.acquire()
                GPIO.output(gpio_num, GPIO.HIGH)
                sleep(1)
                GPIO.output(gpio_num, GPIO.LOW)
                sleep(1)
                mutex.release()
            else:
                GPIO.output(gpio_num, GPIO.LOW)

    def start(self, mutex):
        threading.Thread(target = _button).start()
        threading.Thread(target = light_blink, args = (LED1_PIN, mutex)).start()
        threading.Thread(target = light_blink, args = (LED2_PIN, mutex)).start()
        threading.Thread(target = _servo).start()
        # threading.Thread(target = _buzzer).start()


def main():
    STATE = STATE_NORMAL
    mutex = Lock()

    exp = traffic_system()
    exp.start(mutex)

if __name__ == "__main__": main()
