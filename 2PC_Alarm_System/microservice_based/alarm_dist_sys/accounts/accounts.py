
# account management node server
# stores user info : username, password
# works similar to storage node 


import grpc
import alarm_pb2, alarm_pb2_grpc

import json
from concurrent import futures
import uuid 

FILE = 'saved_users.json'
user_count = 0
sessions = {}


class AccountServicer(alarm_pb2_grpc.AccountServicer):
    def __init__(self):
        self.users = {}
        self.loadSavedUsers()

    # on startup, loads alarms saved in json file
    def loadSavedUsers(self):
        global user_count 
        with open(FILE, "r") as f:
            try:
                data = json.load(f)
                for user_data in data:
                    user = alarm_pb2.User(username=user_data["username"], password=user_data["password"])
                    self.users[user_count] = user
                    user_count+=1
            except json.JSONDecodeError:
                data = []

    # saves all locally stored alarms in json file
    def saveUsers(self):
        data = []
        for u in self.users.values():
            data.append({"username": u.username, "password": u.password})
        with open(FILE, "w") as f:
            json.dump(data, f)

    # adds new user to json file & local storage, returns 0 if failed, 1 if success
    def AddUser(self, request, context):
        user = request
        for u in self.users.values():
            if u.username == user.username:
                return alarm_pb2.Status(success=0)
        self.users[len(self.users)] = user
        self.saveUsers()
        user_token = str(uuid.uuid4())
        sessions[user_token] = user.username
        return alarm_pb2.Status(success=1, token = user_token)

    def VerifyUser(self, request, context):
        user = request
        for u in self.users.values():
            if u.username == user.username:
                if u.password == user.password:
                    user_token = str(uuid.uuid4())
                    sessions[user_token] = user.username
                    return alarm_pb2.Status(success=1, token=user_token)
        return alarm_pb2.Status(success=0)
    
    def GetUser(self, request, context):
        md = dict(context.invocation_metadata())
        token = md.get("token")
        username = sessions.get(token, "")
        return alarm_pb2.Username(username=username)




def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=50))
    alarm_pb2_grpc.add_AccountServicer_to_server(AccountServicer(), server)
    server.add_insecure_port('[::]:50053')
    server.start()
    print("Account service listening on port 50053")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()