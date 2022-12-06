# publisher.py
import RPi.GPIO as GPIO
from datetime import datetime
import time, os, sqlalchemy, pymysql
# Import GCP requirements
from google.cloud import pubsub_v1


from google.cloud.sql.connector import Connector


# Declare Raspberry Pi GPIO Pins
GPIO.setmode(GPIO.BCM)
PIR = 4 #Physical pin: 7
TRIG = 17 #Physical pin: 11
ECHO = 27 #Physical pin: 13
TIME_THRESHOLD = 10 # Measured in seconds
OUTER_RANGE_THRESHOLD = 375 # Measured in centimeters
RANGE_TRIGGER = 50 # Measured in centimeters
delay = 0 # Count up to prevent output message spamming

# Set up I/O declarations
GPIO.setup(TRIG,GPIO.OUT)
GPIO.setup(ECHO,GPIO.IN)
GPIO.setup(PIR,GPIO.IN)
# Set initial value to false (Not measuring anything)
GPIO.output(TRIG, False)


# Declare Auth Credentials
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'csi4160-pisub.json'

# Init Pub/Sub Object & topic
publisher = pubsub_v1.PublisherClient()
topic_path = 'projects/cheon-csi4160-f22/topics/pi-events'

# Begin interations with environment
print("Alarm system active: Monitoring Environment for threats")

def triggerAlarm(type, dist, time_to_trigger):
	# Function Objectives:
	# 1 - Determine Alarm type
	# 2 - Prepare message for Pub/Sub according to [1]
	# 3 - Send message to Pub/Sub topic
	print("ALARM TRIGGERED".center(40, "-"))
	topic_path = 'projects/cheon-csi4160-f22/topics/pi-events'
	time_now = str(datetime.now())

	# [1] Determine Alarm Type
	if type == 'Time-evoked':
		# [2] Create output message to push to pub/sub topic
		data = f"{time_now} - {type} Alarm Detected - Minimum Distance: {dist}"
		data = data.encode('utf-8')
		
		# [3] Send message and show message id
		print("Sending details to Pub/Sub")
		print(f"Message Contents: {data}")
		future = publisher.publish(topic_path, data)
		print(f'Published message ID: {future.result()}')
		

	# [1] Determine alarm type
	elif type == 'Proximity':
		# [2] Create output message to push to pub/sub topic
		data = f'{time_now} - {type} Alarm Detected - Time to trigger: {time_to_trigger}'
		data = data.encode('utf-8')
		
		# [3] Send message and show message id
		print("Sending details to Pub/Sub")
		print(f"Message Contents: {data}")
		future = publisher.publish(topic_path, data)
		print(f'Published message ID: {future.result()}')

# Logic to support sensor logic
while True:
	# Set pin input to variable
	pir_signal=GPIO.input(PIR)
	delay += 1
	# If motion is detected
	if pir_signal==1:
		start_time = time.time() # start timer for time-based alarm
		min_distance = 1000 # Set default min value for reporting purposes
		try:
			while True: # while PIR == Detecting
				print("Motion detected - Measuring")
				# When the signal is detecting something in range and moving
				GPIO.output(TRIG, True)
				time.sleep(0.00001)
				GPIO.output(TRIG, False)
				
				# Math to handle trig-echo time related-distance calculations
				while GPIO.input(ECHO)==0:
					pulse_start = time.time()
				while GPIO.input(ECHO)==1:
					pulse_end = time.time()
				pulse_duration = pulse_end - pulse_start
				distance = pulse_duration * 17150
				distance = round(distance+1.15, 2)
				print(f"Distance: {distance}")
				# Update min distance if new measurement is smaller
				if distance < min_distance:
					min_distance = distance
					print(f"New Minumum Distance: {min_distance}")
				#Track length (in time) the loop has executed for
				end_time = time.time()
				time_counter = end_time - start_time
				print(f"Time counter: {time_counter}")

				if distance<=OUTER_RANGE_THRESHOLD and TIME_THRESHOLD<=time_counter:
					print("Distance:",distance,"cm")
					triggerAlarm('Time-evoked', distance, str(time_counter))
					# Reset trigger variables
					time_counter = 0
					min_distance = 1000
					pir_signal=0
					break

				if distance<=RANGE_TRIGGER:
					triggerAlarm('Proximity', distance, time_counter)
					# Reset Trigger variables
					time_counter = 0
					min_distance = 1000
					pir_signal=0
					break


		except KeyboardInterrupt:
			GPIO.cleanup()
	# If no motion is detected and enough time has passed, print status to the terminal
	if pir_signal==0 and delay >= 50000:
		print("Motion Stopped")
		delay = 0
