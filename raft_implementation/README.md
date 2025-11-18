# Raft Consensus Algorithm Implementation

**Course:** CSE 5306 - Distributed Systems
**Project 3:** Consensus Algorithms (Raft)
**Implementation:** Q3 (Leader Election) and Q4 (Log Replication)

## Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [Requirements](#requirements)
- [Installation and Setup](#installation-and-setup)
- [Running the Implementation](#running-the-implementation)
- [Testing](#testing)
- [Implementation Details](#implementation-details)
- [File Structure](#file-structure)
- [External References](#external-references)

---

## Overview

This project implements the **Raft consensus algorithm** with:

- **Leader Election (Q3):** Nodes elect a leader through randomized timeouts and voting
- **Log Replication (Q4):** Leader replicates log entries to followers and commits when majority confirms
- **Client Forwarding:** Non-leader nodes redirect client requests to the current leader
- **5 Test Cases (Q5):** Comprehensive testing scenarios with Docker containers

The implementation uses **gRPC** for inter-node communication and **Docker** for containerization.

---

## Architecture

### Cluster Configuration
- **5 Raft Nodes:** Each node can be a Follower, Candidate, or Leader
- **Heartbeat Timeout:** 1 second (leader sends periodic heartbeats)
- **Election Timeout:** Randomized between 1.5 and 3 seconds
- **Communication:** gRPC over TCP

### State Machine
The implementation manages a simple polling system:
- `CREATE_POLL`: Create a new poll with question and options
- `VOTE`: Submit a vote for a poll option
- `GET_RESULTS`: Retrieve poll results

### Node States
1. **Follower:** Default state, receives log entries from leader
2. **Candidate:** Competing for leadership during election
3. **Leader:** Handles client requests and replicates log

---

## Requirements

### System Requirements
- **Docker:** Version 20.10 or higher
- **Docker Compose:** Version 1.29 or higher
- **Python 3.10+** (for running test clients locally)

### Python Dependencies (for local testing)
```bash
grpcio==1.60.0
grpcio-tools==1.60.0
protobuf==4.25.1
```

---

## Installation and Setup

### Step 1: Navigate to Project Directory
```bash
cd raft_implementation
```

### Step 2: Generate gRPC Code (Optional - Docker does this automatically)
```bash
# Install Python dependencies
pip install -r requirements.txt

# Generate Python gRPC code from proto file
bash generate_proto.sh

# OR manually:
python3 -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. raft.proto
```

### Step 3: Build Docker Images
```bash
docker-compose build
```

This creates Docker images for all 5 Raft nodes.

---

## Running the Implementation

### Start the Raft Cluster (5 Nodes)

```bash
# Start all 5 nodes
docker-compose up

# OR run in background (detached mode)
docker-compose up -d
```

**Expected Output:**
- Each node starts as a **Follower**
- Within 1.5-3 seconds, one node times out and starts an **election**
- A **Leader** is elected and begins sending heartbeats
- You'll see RPC messages logged:
  ```
  [Node 2] sends RPC RequestVote to Node 1
  [Node 1] runs RPC RequestVote called by Node 2
  [Node 3] sends RPC AppendEntries (heartbeat) to Node 1
  [Node 1] runs RPC AppendEntries (heartbeat) called by Node 3
  ```

### View Logs of Individual Nodes

```bash
# View logs for Node 1
docker logs raft_node1

# View logs for Node 2
docker logs raft_node2

# Follow logs in real-time
docker logs -f raft_node1

# View all logs
docker-compose logs -f
```

### Stop the Cluster

```bash
# Stop all nodes
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

---

## Testing

### Automated Test Suite (Q5 - 5 Test Cases)

The implementation includes 5 comprehensive test cases:

1. **Normal Leader Election:** Verify leader election on startup
2. **Leader Failure and Re-election:** Test failover when leader crashes
3. **Log Replication:** Verify operations are replicated across cluster
4. **Split Vote Recovery:** Test randomized timeout resolution
5. **Node Rejoining:** Test catch-up when partitioned node rejoins

**Run All Tests:**
```bash
# Make sure cluster is running
docker-compose up -d

# Wait 10 seconds for cluster to stabilize
sleep 10

# Generate gRPC code locally (if not done)
python3 -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. raft.proto

# Run test suite
python3 test_cases.py
```

**What the Tests Do:**
- Test 1: Waits for initial leader election
- Test 2: Stops the leader container and verifies new election
- Test 3: Submits multiple operations and verifies commitment
- Test 4: Pauses leader to trigger election with potential split vote
- Test 5: Pauses a follower, submits operations, then rejoins node

**Screenshot Capture:**
Take screenshots during test execution for your report:
- Leader election messages
- RPC call logs (RequestVote, AppendEntries)
- Test case results (PASS/FAIL)

### Interactive Test Client

```bash
# Generate gRPC code locally (if not done)
python3 -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. raft.proto

# Run interactive client
python3 test_client.py
```

**Available Commands:**
```
1 - Create Poll
2 - Vote on Poll
3 - Get Poll Results
4 - Find Leader
q - Quit
```

**Example Session:**
```
Enter command: 1
Poll question: What's your favorite color?
Options (comma-separated): Red, Blue, Green, Yellow

Enter command: 2
Poll ID: poll_1
Option: Blue

Enter command: 3
Poll ID: poll_1
```

### Automated Test Scenario

```bash
# Run automated test scenario
python3 test_client.py --auto
```

This runs a predefined sequence of operations to demonstrate the system.

### Manual Testing with Docker Commands

```bash
# Start cluster
docker-compose up -d

# View which node is leader (check logs)
docker logs raft_node1 | grep "WON ELECTION"
docker logs raft_node2 | grep "WON ELECTION"
docker logs raft_node3 | grep "WON ELECTION"

# Simulate leader failure
docker stop raft_node3  # Replace with actual leader

# Watch re-election
docker logs -f raft_node1

# Restart failed node
docker start raft_node3

# Simulate network partition
docker pause raft_node4
docker unpause raft_node4
```

---

## Implementation Details

### Q3: Leader Election

**Implementation (`raft_node.py`):**

1. **Election Timer (`_election_timer`):**
   - Background thread monitors election timeout
   - Followers/Candidates timeout if no heartbeat received
   - Randomized timeout between 1.5-3 seconds

2. **Start Election (`_start_election`):**
   - Transition to CANDIDATE state
   - Increment term and vote for self
   - Send `RequestVote` RPC to all peers
   - Collect votes and become leader if majority obtained

3. **RequestVote RPC:**
   - Grants vote if candidate's log is up-to-date
   - Only one vote per term per node
   - Resets election timer on vote granted

4. **Become Leader (`_become_leader`):**
   - Transition to LEADER state
   - Initialize `next_index` and `match_index` for followers
   - Start sending periodic heartbeats

5. **Heartbeats (`_send_heartbeats`):**
   - Leader sends `AppendEntries` RPC every 1 second
   - Empty entries = heartbeat
   - Prevents followers from timing out

**RPC Logging Format:**
```
[Node <id>] sends RPC <name> to Node <id>
[Node <id>] runs RPC <name> called by Node <id>
```

### Q4: Log Replication

**Implementation (`raft_node.py`):**

1. **Client Request Handling:**
   - Non-leaders redirect to current leader
   - Leader appends operation to log
   - Returns success when committed by majority

2. **Log Replication (`_send_heartbeats`):**
   - Leader sends `AppendEntries` with log entries
   - Tracks `next_index` for each follower
   - Decrements on failure (inconsistency detection)

3. **Commit Index Update (`_update_commit_index`):**
   - Leader counts replicas for each log entry
   - Commits when majority has replicated
   - Only commits entries from current term

4. **Applying Entries (`_apply_committed_entries`):**
   - Applies committed entries to state machine
   - Executes operations (CREATE_POLL, VOTE, etc.)
   - Updates `last_applied` index

5. **Log Consistency:**
   - Followers check `prev_log_index` and `prev_log_term`
   - Delete conflicting entries
   - Append new entries from leader

### gRPC Service Definition (`raft.proto`)

```protobuf
service RaftNode {
    rpc RequestVote(RequestVoteRequest) returns (RequestVoteResponse);
    rpc AppendEntries(AppendEntriesRequest) returns (AppendEntriesResponse);
    rpc ClientRequest(ClientRequestMessage) returns (ClientRequestResponse);
}
```

**Messages:**
- `RequestVoteRequest/Response`: Leader election
- `AppendEntriesRequest/Response`: Heartbeat and log replication
- `ClientRequestMessage/Response`: Client operations

---

## File Structure

```
raft_implementation/
│
├── raft.proto                 # gRPC service definitions
├── raft_node.py              # Main Raft node implementation (Q3, Q4)
├── test_client.py            # Interactive and automated test client
├── test_cases.py             # 5 test cases for Q5
│
├── requirements.txt          # Python dependencies
├── generate_proto.sh         # Script to generate gRPC code
│
├── Dockerfile                # Docker image for Raft nodes
├── docker-compose.yml        # Orchestration for 5 nodes
│
├── README.md                 # This file
│
└── (Generated files)
    ├── raft_pb2.py           # Generated from raft.proto
    └── raft_pb2_grpc.py      # Generated from raft.proto
```

---

## Troubleshooting

### Issue: No leader elected
**Solution:**
- Wait 5-10 seconds for election timeout
- Check logs: `docker logs raft_node1`
- Verify all 5 nodes are running: `docker ps`

### Issue: "Connection refused" from test client
**Solution:**
- Ensure cluster is running: `docker-compose up -d`
- Check port mappings: `docker ps | grep raft`
- Wait for cluster to stabilize (10 seconds)

### Issue: gRPC module not found
**Solution:**
```bash
pip install grpcio grpcio-tools protobuf
python3 -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. raft.proto
```

### Issue: Docker containers not starting
**Solution:**
```bash
# Clean up old containers
docker-compose down -v

# Rebuild images
docker-compose build --no-cache

# Start fresh
docker-compose up -d
```

---

## External References

This implementation was developed using the following resources:

1. **Raft Paper (Original):**
   - Diego Ongaro and John Ousterhout. "In Search of an Understandable Consensus Algorithm"
   - https://raft.github.io/raft.pdf

2. **Raft Visualization:**
   - https://raft.github.io/
   - Interactive visualization of Raft consensus

3. **Wikipedia - Raft:**
   - https://en.wikipedia.org/wiki/Raft_(algorithm)
   - Provided in assignment

4. **gRPC Documentation:**
   - https://grpc.io/docs/languages/python/
   - Protocol Buffers: https://protobuf.dev/

5. **Docker Documentation:**
   - https://docs.docker.com/
   - Docker Compose: https://docs.docker.com/compose/

6. **Course Materials:**
   - Project 3 assignment document
   - Lecture slides on consensus algorithms

7. **Additional Resources:**
   - "Distributed Systems: Principles and Paradigms" by Andrew S. Tanenbaum
   - https://renjieliu.gitbooks.io/consensus-algorithms-from-2pc-to-raft/ (provided in assignment)

---

## Anything Unusual

### Design Decisions

1. **Simple State Machine:**
   - Implemented a basic polling system instead of generic key-value store
   - Makes testing and demonstration more intuitive
   - Easy to understand operation outcomes

2. **Client Forwarding:**
   - Non-leader nodes return `leader_id` in response
   - Client automatically retries with correct leader
   - Implements automatic leader discovery

3. **Randomized Timeouts:**
   - Each node gets random timeout in [1.5s, 3s] range
   - New random timeout after each election attempt
   - Prevents perpetual split votes

4. **Log Structure:**
   - Operations stored as JSON strings in log entries
   - Flexible for different operation types
   - Easy to extend with new operations

### Known Limitations

1. **Persistence:**
   - State is not persisted to disk
   - Node restart loses all state
   - Production Raft would persist `current_term`, `voted_for`, and `log`

2. **Snapshot/Compaction:**
   - No log compaction implemented
   - Log grows unbounded
   - Production systems would snapshot state periodically

3. **Configuration Changes:**
   - Cluster size is fixed at 5 nodes
   - No dynamic membership changes
   - Raft supports this via joint consensus

4. **Optimizations:**
   - No batch AppendEntries
   - No pipeline optimization
   - Production implementations would optimize RPC usage

---

## Contributors

[Your Name and Student ID]
[Partner Name and Student ID (if applicable)]

**Work Distribution:**
- [Name 1]: Q3 Implementation (Leader Election)
- [Name 2]: Q4 Implementation (Log Replication)
- Both: Q5 Testing, Documentation, Docker configuration

---

## GitHub Repository

[Include your GitHub repository link here]

**Repository Structure:**
```
your-repo/
├── raft_implementation/    # This Raft implementation
├── rest_https/            # Project 2 - REST implementation
├── microservice_rpc/      # Project 2 - gRPC implementation
└── README.md              # Main repository README
```

---

## How to Submit

1. **Test everything:**
   ```bash
   docker-compose up -d
   python3 test_cases.py
   ```

2. **Capture screenshots** of:
   - Leader election process
   - RPC message logs
   - All 5 test cases running
   - Docker containers status

3. **Create report** including:
   - Student names and IDs
   - Work distribution
   - Screenshots of test cases
   - Explanation of implementation
   - Any challenges faced

4. **Zip all files:**
   ```bash
   zip -r raft_implementation.zip raft_implementation/
   ```

5. **Upload to Canvas:**
   - Source code (zip file)
   - Report (PDF)
   - README (this file)

---

## License

This implementation is for educational purposes as part of CSE 5306 - Distributed Systems.

---

**Last Updated:** [Current Date]
**Version:** 1.0
