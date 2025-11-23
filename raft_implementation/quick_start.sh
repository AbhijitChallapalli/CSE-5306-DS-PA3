#!/bin/bash
# Quick Start Script for Raft Implementation

echo "========================================="
echo "  Raft Consensus - Quick Start"
echo "========================================="
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "ERROR: Docker Compose is not installed"
    exit 1
fi

echo "✓ Docker found"
echo ""

# Build images
echo "Building Docker images..."
docker-compose build

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to build images"
    exit 1
fi

echo "✓ Images built"
echo ""

# Start cluster
echo "Starting Raft cluster (5 nodes)..."
docker-compose up -d

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to start cluster"
    exit 1
fi

echo "✓ Cluster started"
echo ""

# Wait for stabilization
echo "Waiting for cluster to stabilize (10 seconds)..."
sleep 10

echo ""
echo "========================================="
echo "  Cluster is ready!"
echo "========================================="
echo ""
echo "View logs:"
echo "  docker logs -f raft_node1"
echo "  docker logs -f raft_node2"
echo "  docker-compose logs -f"
echo ""
echo "Run tests:"
echo "  python3 test_cases.py        # Run all 5 test cases"
echo "  python3 test_client.py       # Interactive client"
echo "  python3 test_client.py --auto  # Automated test"
echo ""
echo "Stop cluster:"

echo "  docker-compose down"
echo ""
echo "Check cluster status:"
echo "  docker ps | grep raft"
echo ""
