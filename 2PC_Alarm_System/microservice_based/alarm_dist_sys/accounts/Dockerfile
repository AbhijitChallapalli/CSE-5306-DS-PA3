# # syntax=docker/dockerfile:1

# FROM python:3.12

# WORKDIR /app
# COPY accounts.py .
# COPY alarm_pb2.py alarm_pb2_grpc.py .

# RUN pip install --no-cache-dir grpcio grpcio-tools protobuf

# CMD ["python", "accounts.py"]
# microservice_based/alarm_dist_sys/accounts/Dockerfile
FROM python:3.12

WORKDIR /app

RUN apt-get update && apt-get install -y nodejs npm && rm -rf /var/lib/apt/lists/*

COPY accounts.py accounts_vote.py .
COPY alarm_pb2.py alarm_pb2_grpc.py alarm.proto .
COPY accounts_decision.js .
#COPY saved_users.json .  # if you persist users

RUN pip install --no-cache-dir grpcio protobuf
RUN npm install @grpc/grpc-js @grpc/proto-loader

CMD ["sh", "-c", "python accounts.py & python -u accounts_vote.py & node accounts_decision.js && wait"]
