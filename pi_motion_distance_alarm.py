# pi_motion_distance_alarm.py
import RPi.GPIO as GPIO
import time

# Declare GPIO Pins
PIR = 4 #Physical pin: 7
TRIG = 17 #Physical pin: 11
ECHO = 27 #Physical pin: 13
TIME_TRHRESHOLD = 10 # Measured in seconds
RANGE_THRESHOLD = 375 # Measured in centimeters
RANGE_TRIGGER = 50 # Measured in centimeters
# Set up I/O declarations
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

# Set initial value to false (Not measuring anything)
GPIO.output(TRIG, False)

def triggerAlarm(type, dist):
    # send mesage to pub/sub
    # Contents:
        # time, type(of trigger), reporting device, dist
    
    # send query to database



# Logic to support Ultrasonic sensor

while True:
    # Wait for the motion detector to activate before attempting to find an object
    pir.wait_for_motion()
    #Action taken:
    # contents of reference for ultrasonic sensor
    # do this until target is out of range

    # if the range < 200cm then we want to start a counter
    # count until time THRESHOLD 
    # if threshold is met / hit, then we triggerAlarm()
    # Create db entry -> prepared statement
    # Send message to pub/sub topic 
    # if the range < 50 cm then we want to trigger the alarm right away
    # Range threshold
    try:
        while True:
            GPIO.output(TRIG, True)
            time.sleep(0.00001)
            GPIO.output(TRIG, False)

            while GPIO.input(ECHO)==0:
                pulse_start = time.time()
            while GPIO.input(ECHO)==1:
                pulse_end = time.time()
            pulse_duration = pulse_end - pulse_start
            distance = pulse_duration * 17150

            distance = round(distance+1.15, 2)
  
            if distance<=RANGE_THRESHOLD and TIME_TRHRESHOLD<=time_counter:
                print("distance:",distance,"cm")
                triggerAlarm('Time-evoked', distance)
                i=1
          
            if distance<=RANGE_TRIGGER:
                triggerAlarm('Proximity', distance)
                i=0
                time.sleep(2)

    except KeyboardInterrupt:
        GPIO.cleanup()

    print("Motion detected - LED Active")
    pir.wait_for_no_motion()
    red_led.off()
    print("Motion Stopped")