# microservice_based/alarm_dist_sys/coordinator/Dockerfile
FROM python:3.12

WORKDIR /app
COPY coordinator.py .
COPY alarm_pb2.py alarm_pb2_grpc.py .

RUN pip install --no-cache-dir grpcio protobuf

CMD ["python", "coordinator.py"]
