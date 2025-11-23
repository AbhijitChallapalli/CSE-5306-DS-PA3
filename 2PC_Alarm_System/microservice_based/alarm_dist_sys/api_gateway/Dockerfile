# syntax=docker/dockerfile:1

FROM python:3.12

WORKDIR /app
COPY api_gateway.py .
COPY alarm_pb2.py alarm_pb2_grpc.py .

RUN pip install --no-cache-dir grpcio grpcio-tools protobuf pytz
RUN pip install --no-cache-dir fastapi uvicorn python-multipart

EXPOSE 8080

CMD ["python", "-m", "uvicorn", "api_gateway:app", "--host", "0.0.0.0", "--port", "8080"]
