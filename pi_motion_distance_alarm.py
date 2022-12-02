# pi_motion_distance_alarm.py
import RPi.GPIO as GPIO
import time, datetime, os, sqlalchemy, pymysql
# Import GCP requirements
from google.cloud import pubsub_v1
from google.cloud.sql.connector import Connector


# Declare Raspberry Pi GPIO Pins
PIR = 4 #Physical pin: 7
TRIG = 17 #Physical pin: 11
ECHO = 27 #Physical pin: 13
TIME_TRHRESHOLD = 10 # Measured in seconds?
OUTER_RANGE_THRESHOLD = 375 # Measured in centimeters
RANGE_TRIGGER = 50 # Measured in centimeters

# Set up I/O declarations
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)
GPIO.setup(PIR, GPIO.IN)

# Set initial value to false (Not measuring anything)
GPIO.output(TRIG, False)

# Initialize connector object
connector = Connector()
# Declare Credential Path
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'csi4160-pisub.json'

# Create Pub/Sub object and set topic path
publisher = pubsub_v1.PublisherClient()
topic_path = 'projects/cheon-csi4160-f22/topics/pi-events'


#Establish connection object construction
def getconn() -> pymysql.connections.Connection:
	with Connector() as connector:
		conn: pymysql.connections.Connection = connector.connect(
			"cheon-csi4160-f22:us-central1:cheon-4160",
			"pymysql",
			user="root",
			password="bowers",
			database="DB_ALARMS",
		)
	return conn


# Create connection pool
pool = sqlalchemy.create_engine(
	"mysql+pymysql://",
	creator=getconn,
)

def triggerAlarm(type, dist, time_to_trigger):
	# Function Objectives:
	# 1 - Determine Alarm type
	# 2 - Prepare queries according to [1]
	# 3 - Prepare message for Pub/Sub according to [1]
	# 4 - Send message to Pub/Sub topic
	# 5 - Connect to DB, execute query, return full table contents

	topic_path = 'projects/cheon-csi4160-f22/tpoics/pi-events'
	timestamp = datetime.now()

	# [1] Determine Alarm Type
	if type == 'Time-evoked':
		# [2] Prepare time alarm query
		insert_stmt = sqlalchemy.text(
			"INSERT INTO time_alarms (time_now, min_distance) VALUES (:timestamp, :min_distance)"
		)

		# [3] Create output message to push to pub/sub topic
		data = f"{timestamp} - {type} Alarm Detected - Minimum Distance: {dist}"
		data = data.encode('utf-8')
		
		# [4] Send message and show message id
		print("Sending details to Pub/Sub")
		future = publisher.publish(topic_path, data)
		print(f'Published message ID: {future.result()}')

		if future.result() != None:
			# [5] Connect to instance, insert collected data
			with pool.connect() as db_conn:
				db_conn.execute(insert_stmt, time_now=timestamp, min_distance="230")
				result = db_conn.execute("SELECT * FROM prox_alarms").fetchall()
				# result = db_conn.execute("SELECT * FROM time_alarms").fetchall()
				for row in result:
					print(row)

	# [1] Determine alarm type
	elif type == 'Proximity':
		# [2] prepare proximity alarm query
		insert_stmt =  sqlalchemy.text(
			"INSERT INTO prox_alarms (time_now, time_to_trigger) VALUES (:timestamp, :time_to_trigger)"
		)
		# [3] Create output message to push to pub/sub topic
		data = f"{timestamp} - {type} Alarm Detected - Time to trigger: {time_to_trigger}"
		data = data.encode('utf-8')
		
		# [4] Send message and show message id
		print("Sending details to Pub/Sub")
		future = publisher.publish(topic_path, data)
		print(f'Published message ID: {future.result()}')

		if future.result() != None:
			# [5] Connect to instance, insert collected data
			with pool.connect() as db_conn:
				db_conn.execute(insert_stmt, time_now=timestamp, time_to_trigger="10s")
				db_conn.execute("SELECT * FROM time_alarms").fetchall()
				# result = db_conn.execute("SELECT * FROM time_alarms").fetchall()
				for row in result:
					print(row)

# Logic to support Ultrasonic sensor
while True:
	# Wait for the motion detector to activate before attempting to find an object
	# pir.wait_for_motion()
	# Action taken:
	# contents of reference for ultrasonic sensor
	# do this until target is out of range

	# if the range < 200cm then we want to start a counter
	# count until time THRESHOLD
	# if threshold is met / hit, then we triggerAlarm()
	# Create db entry -> prepared statement
	# Send message to pub/sub topic
	# if the range < 50 cm then we want to trigger the alarm right away
	# Range threshold
	pir_signal=GPIO.input(PIR)
	if pir_signal==1:
		start_time = time.time() # start timer for time-based alarm
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
				#Track length (in time) the loop has executed for
				end_time = time.time()
				time_counter= end_time - start_time
				print(f"Time counter: {time_counter}")

				if distance<=OUTER_RANGE_THRESHOLD and TIME_TRHRESHOLD<=time_counter:
					print("Distance:",distance,"cm")
					triggerAlarm('Time-evoked', distance)
					i=1

				if distance<=RANGE_TRIGGER:
					triggerAlarm('Proximity', distance)
					i=0
					time.sleep(2)


		except KeyboardInterrupt:
			GPIO.cleanup()

	if pir_signal==0:
		print("Motion Stopped")