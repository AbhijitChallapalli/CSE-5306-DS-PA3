## storage service/node server 
## will attempt to store alarms in local storage
## currently uses alarm_count to store IDs, not sure if we want to change
## can be run using python node1.py, test1.py calls all rpcs

import grpc
from concurrent import futures
from google.protobuf import empty_pb2
import json
from datetime import datetime, timedelta
from google.protobuf.timestamp_pb2 import Timestamp

import alarm_pb2
import alarm_pb2_grpc

alarm_count = 0
FILE = 'saved_alarm.json'

class StorageServicer(alarm_pb2_grpc.StorageServicer):
    def __init__(self):
        self.alarms = {}
        self.alarm_count = 1
        self.loadSavedAlarms()

    # on startup, loads saved alarms from json file
    def loadSavedAlarms(self):
        global alarm_count
        with open(FILE, "r") as f:
            try:
                data = json.load(f)
                for alarm_data in data:
                    alarm_count+=1
                    now = datetime.now()
                    alarm_time = datetime.fromtimestamp(int(alarm_data["time"]))
                    while (alarm_time < now):
                        alarm_time += timedelta(days=1)
                    trigger_time = Timestamp()
                    trigger_time.seconds = int(alarm_time.timestamp())
                    alarm = alarm_pb2.Alarm(id=alarm_count, user=alarm_data["user"], title=alarm_data["title"], time=trigger_time)
                    self.alarms[alarm.id] = alarm
            except json.JSONDecodeError:
                print("File is empty or contains invalid JSON.")
                data = []
        print(f"Loaded {len(self.alarms)} alarms from {FILE}")

    # saves all locally stored alarms in json file
    def saveAlarms(self):
        data = []
        for alarm in self.alarms.values():
            data.append({"id": alarm.id, "user":alarm.user, "title": alarm.title, "time": alarm.time.seconds})
        with open(FILE, "w") as f:
            json.dump(data, f)

    # adds new alarm to json file and local storage
    def AddAlarm(self, request, context):
        print("Alarm Added in Storage")
        global alarm_count
        alarm = request
        if alarm.id == 0:                   # increment alarm count only if new alarm
            alarm_count+=1
            alarm.id = alarm_count          # set new alarm ID to alarm_count
        self.alarms[alarm.id] = alarm       # store new alarm locally
        self.saveAlarms()
        return empty_pb2.Empty()

    # is called with alarm id
    def GetAlarm(self, request, context):
        alarm_id = request.id
        alarm = self.alarms.get(alarm_id)
        if not alarm:
            return alarm_pb2.Alarm()  # alarm with alarm_id doesnt exist
        return alarm

    def ListAlarms(self, request, context):  # streams the current alarms
        for alarm in self.alarms.values():  
                yield alarm

    # deletes alarm from json file storage and local storage
    def DeleteAlarm(self, request, context):
        alarm_id = request.id
        if alarm_id in self.alarms:
            del self.alarms[alarm_id]
            self.saveAlarms()
        return empty_pb2.Empty()

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=50))
    alarm_pb2_grpc.add_StorageServicer_to_server(StorageServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Storage service listening on port 50051")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()