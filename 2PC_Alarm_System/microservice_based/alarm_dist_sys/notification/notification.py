

# Notification node/service client only
# will handle creating the notifications ?
# not sure what this will look like with the api tho


import grpc
from google.protobuf import empty_pb2

import alarm_pb2, alarm_pb2_grpc
import requests
import threading
import time

API_GATEWAY_URL = "http://api_gateway:8080/notify"

# continuously checks for due alarms from scheduler node
def run_notification_client():
    time.sleep(5)   # ensures scheduler is alive before connecting
    scheduler_channel = grpc.insecure_channel('scheduler:50052')
    scheduler_stub = alarm_pb2_grpc.SchedulerStub(scheduler_channel)
    while True:
        try:
            alarm = scheduler_stub.FwdDueAlarm(empty_pb2.Empty())  # blocks until alarm is due
            postAlarm(alarm)
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.NOT_FOUND:
                time.sleep(1)        # no alarms 
                continue
        time.sleep(0.5)

# fwds due alarm to the API
def postAlarm(alarm):
    data = {"id": alarm.id, "user": alarm.user, "title": alarm.title, "time": alarm.time.seconds}
    try:
        requests.post(API_GATEWAY_URL, json=data)
    except Exception as e:
        print("Notification failed to send to API:", e)



if __name__ == "__main__":
    print("starting notification client")
    t = threading.Thread(target=run_notification_client, daemon=True)
    t.start()
    t.join()