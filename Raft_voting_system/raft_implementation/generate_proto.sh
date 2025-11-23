#!/bin/bash
# Generate Python gRPC code from proto file

python3 -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. raft.proto

echo "Generated raft_pb2.py and raft_pb2_grpc.py"
