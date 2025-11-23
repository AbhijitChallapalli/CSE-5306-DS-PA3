FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy proto file and generate gRPC code
COPY raft.proto .
RUN python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. raft.proto

# Copy node implementation
COPY raft_node.py .

# Make script executable
RUN chmod +x raft_node.py

# Default command (node_id will be passed as argument)
ENTRYPOINT ["python", "raft_node.py"]
