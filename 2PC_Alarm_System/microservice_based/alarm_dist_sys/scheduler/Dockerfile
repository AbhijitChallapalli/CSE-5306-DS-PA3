FROM python:3.12

WORKDIR /app

# Install Node.js + npm
RUN apt-get update && apt-get install -y nodejs npm && rm -rf /var/lib/apt/lists/*

# Copy Python files
COPY scheduler.py scheduler_vote.py .
COPY alarm_pb2.py alarm_pb2_grpc.py alarm.proto .

# Copy Node DecisionPhase
COPY scheduler_decision.js .

RUN pip install --no-cache-dir grpcio protobuf

# Install Node deps
RUN npm install @grpc/grpc-js @grpc/proto-loader

CMD ["sh", "-c", "python scheduler.py & python -u scheduler_vote.py & node scheduler_decision.js && wait"]
