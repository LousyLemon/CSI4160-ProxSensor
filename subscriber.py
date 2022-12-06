#!/bin/python
from google.cloud.sql.connector import Connector
import os, sqlalchemy, pymysql
from google.cloud import pubsub_v1
from google.cloud.sql.connector import Connector
from concurrent.futures import TimeoutError
# Make sure to install mgp123 before using this implementation

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'csi4160-pisub.json'

subscriber = pubsub_v1.SubscriberClient()
subscription_path = 'projects/cheon-csi4160-f22/topics/pi-events'

timeout = 5
soundfile = "alarm.mp3"

def getconn() -> pymysql.connections.Connection:
    with Connector() as connector:
        conn = connector.connect(
            "cheon-csi4160-f22:us-central1:cheon-4160",
            "pymysql",
            user="root",
            password="bowers",
            db="DB_ALARMS",
        )
    return conn

pool = sqlalchemy.create_engine(
    "mysql+pymysql://",
    creator=getconn(),
    )


def prepare_query(type, time_now, content):
    if type.lower == "proximity":
        insert_stmt = sqlalchemy.Text(
            "INSERT INTO prox_alarms (time_now, min_distance) VALUES (:time_now, :min_distance)",
        )
        with pool.connect as db_conn:
            db_conn.execute(insert_stmt, time_now=time_now, min_distance=content)
            result = db_conn.execute("SELECT * FROM prox_alarms")
            for row in result:
                print(row)

    elif type.lower == "time-evoked":
        insert_stmt = sqlalchemy.Text(
            "INSERT INTO time_alarms (time_now, time_to_trigger) VALUES (:time_now, :time_to_trigger)"
        )
        with pool.connect as db_conn:
            db_conn.execute(insert_stmt, time_now=time_now, min_distance=content)
            result = db_conn.execute("SELECT * FROM time_alarms")
            for row in result:
                print(row)

def delayAlarm():
    global alarmed
    alarmed = alarmed + 1
    if alarmed ==1:
        os.system("mpg -C --quiet -n 200 " + soundfile)
    elif alarmed == 5:
        alarmed = 0
    else:
        print("Queue overloaded! Please wait...")

def callback(message):
    print(f'Received message: {message}')
    print(f'Data: {message.data}')
    message.ack()
    delayAlarm()
    global dataList
    dataList = str(message.data)
    date = dataList[0]
    date2 = f'{date} {dataList[1]}'
    prepare_query(dataList[3], date2, dataList[10])

streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
print(f'Listenting for messages on {subscription_path}')

with subscriber:
    try:
        streaming_pull_future.result()
    except TimeoutError:
        streaming_pull_future.cancel()
        streaming_pull_future.result()
