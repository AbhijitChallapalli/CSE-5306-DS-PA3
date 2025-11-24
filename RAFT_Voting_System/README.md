# Raft Consensus Protocol – Polling System Implementation

This project implements the **Raft Consensus Algorithm** for a distributed polling/voting system.

The system consists of multiple nodes that communicate via **gRPC**, orchestrated with **Docker Compose**. Raft ensures **fault-tolerant consensus** through leader election, log replication, and consistent state management across all nodes.

## `GitHub link`: https://github.com/AbhijitChallapalli/CSE-5306-DS-PA3
---

## How to Run

Clone the repository using this command:

```bash
git clone https://github.com/AbhijitChallapalli/CSE-5306-DS-PA3
```

Change directories:

```bash
cd CSE-5306-DS-PA3

cd RAFT_Voting_System

cd raft_integration
```

### Build and Start the Cluster

From the `raft_integration` directory:

```bash
docker compose build
```

Run the services:

```bash
docker compose up
```

This will start a 5-node Raft cluster (Node 1 through Node 5).

### Running Test Scenarios

In a separate terminal, run the comprehensive test suite:

Change directories:

```bash
cd CSE-5306-DS-PA3

cd RAFT_Voting_System

cd raft_integration
```

```bash
python3 test_raft_scenarios.py
```

The test script will automatically:
- Wait for cluster stabilization (10 seconds)
- Run 5 different Raft scenario tests
- Verify consensus, consistency, and replication

---
---

## Viewing Logs

### Per-Node Logs

In separate terminals: for each terminal change directories

Change directories:

```bash
cd CSE-5306-DS-PA3

cd RAFT_Voting_System

cd raft_integration
```

```bash
# Node 1 logs
docker logs -f raft_polling_node1

# Node 2 logs
docker logs -f raft_polling_node2

# Node 3 logs
docker logs -f raft_polling_node3

# Node 4 logs
docker logs -f raft_polling_node4

# Node 5 logs
docker logs -f raft_polling_node5
```

### All Logs Combined

```bash
docker compose logs -f
```

Use `Ctrl + C` to stop following logs.

### Stop the Cluster

```bash
docker compose down
```

---
## Architecture Overview

### Node Structure

Each node in the cluster runs:
- **Raft Protocol Implementation**
  - Leader election with randomized timeouts (1.5s - 3.0s)
  - Heartbeat mechanism (AppendEntries RPCs)
  - Log replication and commit logic
  
- **Polling Service Implementation**
  - CreatePoll, CastVote, GetPollResults, ClosePoll, ListPolls RPCs
  - All write operations go through Raft consensus
  - Read operations can be served by any node after commit

### Raft Implementation Details

#### Configuration
- **Cluster Size**: 5 nodes
- **Heartbeat Timeout**: 1 second
- **Election Timeout**: Randomized between 1.5 - 3.0 seconds
- **Ports**: 
  - Node 1: `50051`
  - Node 2: `50052`
  - Node 3: `50053`
  - Node 4: `50054`
  - Node 5: `50055`

#### Node States
- **FOLLOWER**: Default state; responds to RPCs from leader and candidates
- **CANDIDATE**: Initiates leader election when election timeout expires
- **LEADER**: Handles client requests, replicates log entries to followers

#### Key RPCs
1. **RequestVote**: Used during leader election
2. **AppendEntries**: Used for heartbeats and log replication

#### Polling Operations as Raft Log Entries
- `CREATE_POLL`: Creates a new poll (replicated via Raft)
- `CAST_VOTE`: Records a vote (replicated via Raft)
- `CLOSE_POLL`: Closes a poll (leader-only operation, replicated via Raft)
- `GET_POLL_RESULTS`: Read-only operation (served from local state)
- `LIST_POLLS`: Read-only operation (served from local state)

---

## How Raft Works in This System

### 1. Leader Election

When the cluster starts:
```text
[Node 1] Initialized Raft-Polling Node as FOLLOWER
[Node 1] Election timeout: 2.48s
[Node 1] Started election timer thread
[Node 1] Waiting for election...
```

When a node's election timeout expires, it becomes a candidate:
```text
Node 1 runs RPC RequestVote called by Node 5
[Node 1] Granted vote to Node 5
```

Once a candidate receives majority votes, it becomes the leader and starts sending heartbeats.

### 2. Log Replication (Write Operations)

When a client sends a write request (e.g., CreatePoll) to any node:

**If it's a follower:**
```text
[Node 1] Received CreatePoll request
[Node 1] Forwarding to leader Node 5
Node 1 sends RPC CreatePoll to Node 5
```

**Leader processes the request:**
1. Appends entry to its log
2. Replicates to all followers via AppendEntries RPCs
3. Waits for majority acknowledgment
4. Commits the entry
5. Applies to state machine

**Follower receives and processes:**
```text
Node 1 runs RPC AppendEntries called by Node 5
[Node 1] Q4 STEP 4: Follower copied 1 entries to log
[Node 1] Q4 STEP 5: Updated commit index c: 0 → 1
[Node 1] Q4 EXECUTE: Applied entry 1: CREATE_POLL
```

### 3. Consistency Guarantee

All nodes maintain consistent state after commit:
- Votes are replicated across all nodes
- Any node can serve read requests with consistent results
- Write operations are serialized through the leader

---

## Test Scenarios

The `test_raft_scenarios.py` script validates the following Raft behaviors:

### TEST 1: Leader Discovery & Poll Creation via Any Node
- **Validates**: Client can contact any node; requests are forwarded to leader
- **Expected**: Poll successfully created and replicated

### TEST 2: Log Replication & Consistent Votes Across Nodes
- **Validates**: Multiple votes are replicated and consistently applied
- **Expected**: All nodes report identical vote counts

### TEST 3: Read Consistency from Every Node
- **Validates**: Read operations return consistent results from any node
- **Expected**: All nodes return identical poll results

### TEST 4: Replicated Poll Metadata via ListPolls
- **Validates**: Poll metadata is replicated across all nodes
- **Expected**: All nodes return the same list of polls

### TEST 5: Leader-only ClosePoll & Client Retry Behavior
- **Validates**: Write operations are processed by leader; followers forward requests
- **Expected**: Poll is successfully closed via leader



## What to Look For

### 1. Leader Election

Expected flow:
```text
[Node X] Initialized Raft-Polling Node as FOLLOWER
[Node X] Election timeout: X.XXs
[Node X] Started election timer thread
...
Node Y runs RPC RequestVote called by Node Z
[Node Y] Granted vote to Node Z
```

### 2. Heartbeat Messages (Steady State)

After a leader is elected, you'll see periodic heartbeats:
```text
Node 1 runs RPC AppendEntries called by Node 5
Node 1 runs RPC AppendEntries called by Node 5
Node 1 runs RPC AppendEntries called by Node 5
...
```

### 3. Write Operation (e.g., CreatePoll)

**On follower:**
```text
[Node 1] Received CreatePoll request
[Node 1] Forwarding to leader Node 5
Node 1 sends RPC CreatePoll to Node 5
```

**Log replication to followers:**
```text
Node 1 runs RPC AppendEntries called by Node 5
[Node 1] Q4 STEP 4: Follower copied 1 entries to log
Node 1 runs RPC AppendEntries called by Node 5
[Node 1] Q4 STEP 5: Updated commit index c: 0 → 1
[Node 1] Q4 EXECUTE: Applied entry 1: CREATE_POLL
```

### 4. Vote Casting (Multiple Operations)

```text
[Node 1] Forwarding to leader Node 5
Node 1 sends RPC CastVote to Node 5
Node 1 runs RPC AppendEntries called by Node 5
[Node 1] Q4 STEP 4: Follower copied 1 entries to log
[Node 1] Q4 STEP 5: Updated commit index c: 1 → 2
[Node 1] Q4 EXECUTE: Applied entry 2: CAST_VOTE
```

### 5. Test Output

When running tests, you should see:
```text
============================================================
TEST 1: Raft – Leader Discovery & Poll Creation via Any Node
============================================================
✓ SUCCESS on Node 1!
  Poll UUID: [UUID]
  Status: open
✓ TEST 1 PASSED

============================================================
TEST 2: Raft – Log Replication & Consistent Votes Across Nodes
============================================================
✓ All nodes report consistent results matching expected counts.
✓ TEST 2 PASSED

...

============================================================
RAFT SCENARIO TEST SUMMARY
============================================================
All 5 Raft scenario tests completed successfully!
```

---

## Key Features Demonstrated

✓ **Leader Election**: Automatic election with randomized timeouts  
✓ **Heartbeat Mechanism**: Periodic AppendEntries RPCs from leader  
✓ **Log Replication**: Write operations replicated to all nodes  
✓ **Commit Protocol**: Majority consensus before applying entries  
✓ **Request Forwarding**: Followers forward writes to leader  
✓ **Read Consistency**: All nodes serve consistent read results  
✓ **Fault Tolerance**: System continues with majority of nodes  

---

## Prerequisites

- **Docker** and **Docker Compose** installed
- **Python 3.x** (for running test script)
- Ports `50051-50055` available

---

## File Structure

```
raft_integration/
├── docker-compose.yml          # Docker orchestration
├── Dockerfile                  # Container image definition
├── raft.proto                  # Raft protocol definitions (RequestVote, AppendEntries)
├── polling.proto               # Polling service definitions
├── raft_pb2.py                 # Generated Raft protobuf code
├── raft_pb2_grpc.py            # Generated Raft gRPC code
├── polling_pb2.py              # Generated Polling protobuf code
├── polling_pb2_grpc.py         # Generated Polling gRPC code
├── raft_polling_node.py        # Main node implementation (Raft + Polling)
└── test_raft_scenarios.py      # Comprehensive test suite
```

---

## Troubleshooting

### Cluster doesn't stabilize
- Wait 10-15 seconds for leader election to complete
- Check that all 5 containers are running: `docker ps`

### Tests fail with connection errors
- Ensure cluster is fully up: `docker compose up -d && sleep 10`
- Verify all nodes are healthy: `docker compose ps`

### Inconsistent state across nodes
- This should not happen if Raft is working correctly
- Check logs for errors in log replication
- Verify majority (3+) nodes are running

---

## Implementation Notes

- **Language**: Python
- **RPC Framework**: gRPC
- **Containerization**: Docker & Docker Compose
- **Consensus**: Raft algorithm (simplified)
- **Application**: Distributed polling/voting system

---
## Contributions
- Srinivasa Sai Abhijit Challapalli - 1002059486 - Implemented the entire 2PC Algorithm, along with README and report (Q1, Q2)
- Namburi Chaitanya Krishna - 1002232417 - Implemented RAFT Algorithm along with the test cases, along with README and report (Q3, Q4, Q5)
---
## References:
- Distributed Alarm Systems GitHub - https://github.com/hoaihdinh/Distributed-Alarm-System/
- Distributed Voting System GitHub - https://github.com/CSE-5306-004-DISTRIBUTED-SYSTEMS/Project2
---
## External Resources Referenced

- Raft Consensus Algorithm: https://raft.github.io/
- gRPC Documentation: https://grpc.io/docs/
- Docker Compose Documentation: https://docs.docker.com/compose/

---

