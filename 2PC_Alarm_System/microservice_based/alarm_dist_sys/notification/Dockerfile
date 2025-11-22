# syntax=docker/dockerfile:1

FROM python:3.12

WORKDIR /app
COPY notification.py .
COPY alarm_pb2.py alarm_pb2_grpc.py .

RUN pip install --no-cache-dir grpcio grpcio-tools protobuf requests

CMD ["python", "-u", "notification.py"]
