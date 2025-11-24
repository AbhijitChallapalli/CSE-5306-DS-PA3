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

## Contact

For questions or issues:
- Abhijit Challapalli: sxc9486@mavs.uta.edu
- Chaitanya Krishna Namburi: cxn2417@mavs.uta.edu


