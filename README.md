# CSE 5306 - Distributed Systems - Programming Assignment 3

## Consensus Algorithms: 2PC and Raft Implementation

This repository contains implementations of two fundamental distributed consensus algorithms:
- **Two-Phase Commit (2PC)** - Applied to a distributed alarm system
- **Raft Consensus Algorithm** - Applied to a distributed polling/voting system

Both implementations use **gRPC** for inter-node communication and **Docker Compose** for containerization and orchestration.

## `GitHub Repository`: https://github.com/AbhijitChallapalli/CSE-5306-DS-PA3

---

## Project Structure

```
CSE-5306-DS-PA3/
├── 2PC_Alarm_System/
│   └── microservice_based/        # 2PC implementation (Q1, Q2)
│       ├── alarm_dist_sys/        # Microservices code
│       ├── docker-compose.yml     # Docker orchestration
│       └── README.md              # Detailed 2PC documentation
│
└── RAFT_Voting_System/
    └── raft_integration/          # Raft implementation (Q3, Q4, Q5)
        ├── raft_polling_node.py   # Main Raft node implementation
        ├── test_raft_scenarios.py # Comprehensive test suite
        ├── docker-compose.yml     # Docker orchestration
        └── README.md              # Detailed Raft documentation
```

---

## Project Overview

### 1. Two-Phase Commit (2PC) - Alarm System

**Location**: `2PC_Alarm_System/microservice_based/`

**Implementation**: Microservice-based alarm system with 2PC for distributed transactions

**Key Features**:
- ✓ Two-phase commit protocol for "Add Alarm" operations
- ✓ Coordinator-participant architecture
- ✓ Voting phase and decision phase implementation
- ✓ Python (coordinator, vote phase) + Node.js (decision phase)
- ✓ Web UI for alarm management (FastAPI)
- ✓ Global commit and global abort scenarios

**Microservices**:
- API Gateway (port 8080) - Web interface
- Coordinator (port 60050) - 2PC orchestrator
- Scheduler (ports 60052, 61052) - Participant
- Accounts (ports 60053, 61053) - Participant
- Storage (port 50051) - Persistent storage
- Notification - Alert service

**Quick Start**:
```bash
cd 2PC_Alarm_System/microservice_based
docker compose build
docker compose up
```

Then open: http://localhost:8080

**[→ View Full 2PC Documentation](2PC_Alarm_System/microservice_based/README.md)**

---

### 2. Raft Consensus - Polling System

**Location**: `RAFT_Voting_System/raft_integration/`

**Implementation**: Distributed polling system with Raft consensus

**Key Features**:
- ✓ Leader election with randomized timeouts
- ✓ Log replication and commit protocol
- ✓ Heartbeat mechanism (AppendEntries RPCs)
- ✓ Request forwarding from followers to leader
- ✓ Consistent reads from any node
- ✓ Fault-tolerant consensus (5-node cluster)
- ✓ Comprehensive test suite with 5 scenarios

**Raft Operations**:
- CreatePoll, CastVote, ClosePoll (write operations via Raft)
- GetPollResults, ListPolls (read operations from any node)

**Quick Start**:
```bash
cd RAFT_Voting_System/raft_integration
docker compose build
docker compose up
```

In another terminal:
```bash
python3 test_raft_scenarios.py
```

**[→ View Full Raft Documentation](RAFT_Voting_System/raft_integration/README.md)**

---

## Assignment Questions Mapping

### Q1: 2PC Voting Phase [✓ Completed]
- **Location**: `2PC_Alarm_System/microservice_based/`
- **Files**: `coordinator.py`, `scheduler_vote.py`, `accounts_vote.py`
- **Details**: Implemented vote-request and vote-commit/vote-abort messages between coordinator and participants

### Q2: 2PC Decision Phase [✓ Completed]
- **Location**: `2PC_Alarm_System/microservice_based/`
- **Files**: `coordinator.py`, `scheduler_decision.js`, `accounts_decision.js`
- **Details**: Implemented global-commit and global-abort decision propagation with proper logging

### Q3: Raft Leader Election [✓ Completed]
- **Location**: `RAFT_Voting_System/raft_integration/`
- **Files**: `raft_polling_node.py` (election logic)
- **Details**: Implemented RequestVote RPC, randomized election timeouts (1.5-3s), and heartbeat mechanism (1s)

### Q4: Raft Log Replication [✓ Completed]
- **Location**: `RAFT_Voting_System/raft_integration/`
- **Files**: `raft_polling_node.py` (log replication logic)
- **Details**: Implemented AppendEntries RPC, log copying, commit index updates, and request forwarding

### Q5: Raft Test Scenarios [✓ Completed]
- **Location**: `RAFT_Voting_System/raft_integration/`
- **Files**: `test_raft_scenarios.py`
- **Details**: 5 comprehensive test cases validating leader discovery, log replication, read consistency, metadata replication, and leader-only writes

---

## Prerequisites

### Required Software
- **Docker** and **Docker Compose**
- **Python 3.x** (for Raft tests)
- **Git** (for cloning repository)

### Required Ports

**2PC System**:
- 8080 - API Gateway (Web UI)
- 50051 - Storage
- 50052 - Scheduler
- 50053 - Accounts
- 60050 - Coordinator
- 60052, 61052 - Scheduler Vote/Decision
- 60053, 61053 - Accounts Vote/Decision

**Raft System**:
- 50051-50055 - Raft nodes 1-5

---

## How to Run Both Projects

### Option 1: Run Sequentially

**Run 2PC first:**
```bash
cd 2PC_Alarm_System/microservice_based
docker compose up
# Test via web UI at http://localhost:8080
# Press Ctrl+C when done
docker compose down
cd ../..
```

**Then run Raft:**
```bash
cd RAFT_Voting_System/raft_integration
docker compose up
# In another terminal: python3 test_raft_scenarios.py
# Press Ctrl+C when done
docker compose down
```

### Option 2: Run Separately

Each project can be run independently. See individual README files for detailed instructions.

---

## Key Technologies

| Component | Technology |
|-----------|-----------|
| **Communication** | gRPC (Protocol Buffers) |
| **Containerization** | Docker, Docker Compose |
| **Languages** | Python 3.x, Node.js |
| **2PC Web Framework** | FastAPI, Uvicorn |
| **Consensus Algorithms** | 2PC, Raft |

---

## Demonstration Guide

### For 2PC (Questions 1-2)

1. Start the system:
   ```bash
   cd 2PC_Alarm_System/microservice_based
   docker compose up
   ```

2. Open browser to http://localhost:8080 and login

3. **Test Global Commit**:
   - Add alarm with title "test alarm" or any normal name
   - Watch coordinator logs: `docker compose logs -f coordinator`
   - Verify alarm appears in dashboard

4. **Test Global Abort**:
   - Add alarm with title starting with "abort" (e.g., "abort test")
   - Watch logs show VOTE_ABORT → GLOBAL_ABORT flow
   - Verify alarm does NOT appear in dashboard

### For Raft (Questions 3-5)

1. Start the cluster:
   ```bash
   cd RAFT_Voting_System/raft_integration
   docker compose up
   ```

2. Watch logs to see leader election:
   ```bash
   docker logs -f raft_polling_node1
   ```

3. Run comprehensive tests:
   ```bash
   python3 test_raft_scenarios.py
   ```

4. Observe:
   - Leader election messages
   - Heartbeat (AppendEntries) messages
   - Log replication for CreatePoll and CastVote
   - Consistent results across all 5 nodes

---

## Important Notes

### 2PC Implementation
- 2PC is **only applied** to the "Add Alarm" operation
- Delete/List operations bypass 2PC (direct storage access)
- Title starting with "abort" triggers intentional vote abort for demonstration
- Vote and Decision phases use separate processes (Python + Node.js)
- All logs are properly formatted as per assignment requirements

### Raft Implementation
- 5-node cluster with automatic leader election
- Randomized election timeouts prevent split votes
- All write operations go through leader
- Read operations served from any node (after commit)
- Client requests can go to any node (auto-forwarding to leader)
- Proper logging of all RPC calls as per assignment requirements

---

## Logging Format

Both implementations follow the required logging format:

**2PC Logging**:
```text
Phase <phase_name> of Node <node_id> sends RPC <rpc_name> to Phase <phase_name> of Node <node_id>
```

**Raft Logging**:
```text
Node <node_id> sends RPC <rpc_name> to Node <node_id>
Node <node_id> runs RPC <rpc_name> called by Node <node_id>
```

---

## Team Contributions

### Srinivasa Sai Abhijit Challapalli - 1002059486
- Implemented complete 2PC algorithm (Q1, Q2)
- Voting phase and decision phase implementation
- Microservice architecture design
- 2PC documentation and testing

### Namburi Chaitanya Krishna - 1002232417
- Implemented complete Raft algorithm (Q3, Q4, Q5)
- Leader election and log replication
- Comprehensive test suite (5 scenarios)
- Raft documentation and testing

---

## References

### Base Implementations
- Distributed Alarm System: https://github.com/hoaihdinh/Distributed-Alarm-System/
- Distributed Voting System: https://github.com/CSE-5306-004-DISTRIBUTED-SYSTEMS/Project2

### Technical Resources
- Raft Consensus Algorithm: https://raft.github.io/
- Raft Paper: https://raft.github.io/raft.pdf
- gRPC Documentation: https://grpc.io/docs/
- Docker Compose Documentation: https://docs.docker.com/compose/
- Two-Phase Commit: Distributed Systems: Principles and Paradigms (Tanenbaum & Van Steen)

---

## Troubleshooting

### Port Conflicts
- Ensure no other services are using required ports
- Use `docker ps` to check running containers
- Use `lsof -i :<port>` to find processes using specific ports

### Docker Issues
- Clear containers: `docker compose down`
- Remove all containers: `docker system prune -a`
- Rebuild from scratch: `docker compose build --no-cache`

### Network Issues
- Ensure Docker network is properly configured
- Check that all containers are on the same network
- Verify container names resolve properly

### 2PC-Specific
- If web UI doesn't load, check if port 8080 is available
- For login issues, use: username="admin", password="12345"
- Check coordinator logs if 2PC transactions fail

### Raft-Specific
- Allow 10-15 seconds for leader election to complete
- Ensure at least 3 nodes are running for majority consensus
- If tests fail, verify cluster is fully up before running tests

---

## Course Information

**Course**: CSE 5306 - Distributed Systems  
**Assignment**: Programming Assignment 3  
**Topic**: Consensus Algorithms (2PC and Raft)  
**Institution**: University of Texas at Arlington

---

## License

This project is submitted as part of academic coursework for CSE 5306.

---

## Contact

For questions or issues:
- Abhijit Challapalli: sxc9486@mavs.uta.edu
- Chaitanya Krishna Namburi: cxn2417@mavs.uta.edu

---

