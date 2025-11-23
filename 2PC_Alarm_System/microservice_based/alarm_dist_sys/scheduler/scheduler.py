## scheduler service node server


import grpc
from concurrent import futures
from google.protobuf import empty_pb2
import time
import asyncio


import alarm_pb2
import alarm_pb2_grpc

#delete later
import json
import os
from datetime import datetime



class SchedulerServicer(alarm_pb2_grpc.SchedulerServicer):
    def __init__(self):
        self.storage_channel = grpc.aio.insecure_channel("storage:50051")  
        self.storage_stub = alarm_pb2_grpc.StorageStub(self.storage_channel)
        self.account_channel = grpc.insecure_channel("accounts:50053")
        self.account_stub = alarm_pb2_grpc.AccountStub(self.account_channel)

    # fwds request for new alarm
    async def ScheduleAlarm(self, request, context):
        await self.storage_stub.AddAlarm(request)
        return empty_pb2.Empty()

    # sends due alarm to the notification service
    async def FwdDueAlarm(self, request, context):
        now = int(time.time())
        async for alarm in self.storage_stub.ListAlarms(empty_pb2.Empty()):
            if alarm.time.seconds <= now:
                self.storage_stub.DeleteAlarm(alarm_pb2.AlarmId(id=alarm.id))
                return alarm  
        # No alarms due
        context.abort(grpc.StatusCode.NOT_FOUND, "No alarms due")
                

async def serve():
    server = grpc.aio.server()
    alarm_pb2_grpc.add_SchedulerServicer_to_server(SchedulerServicer(), server)
    server.add_insecure_port("[::]:50052")
    await server.start()
    print(f"Scheduler service listening on port 50052")
    await server.wait_for_termination()


if __name__ == "__main__":
    asyncio.run(serve())