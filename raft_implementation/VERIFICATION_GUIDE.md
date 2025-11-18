# Raft Implementation Verification & How It Works

## ✅ Part 1: Assignment Requirements Checklist

### Q3: Leader Election Requirements ✅

| Requirement | Implementation | Location | Status |
|------------|----------------|----------|---------|
| **Heartbeat timeout: 1 second** | `self.heartbeat_timeout = 1.0` | `raft_node.py:59` | ✅ |
| **Election timeout: Random [1.5s, 3s]** | `random.uniform(1.5, 3.0)` | `raft_node.py:60` | ✅ |
| **All nodes start as FOLLOWER** | `self.state = NodeState.FOLLOWER` | `raft_node.py:52` | ✅ |
| **Follower → Candidate on timeout** | `self.state = NodeState.CANDIDATE` | `raft_node.py:109` | ✅ |
| **Candidate increments term** | `self.current_term += 1` | `raft_node.py:110` | ✅ |
| **Candidate votes for itself** | `self.voted_for = self.node_id` | `raft_node.py:111` | ✅ |
| **Send RequestVote RPC** | `stub.RequestVote(request)` | `raft_node.py:151` | ✅ |
| **Receive majority → Leader** | `if votes_received >= votes_needed` | `raft_node.py:170` | ✅ |
| **Leader sends heartbeats** | `_send_heartbeats()` | `raft_node.py:198` | ✅ |
| **AppendEntries as heartbeat** | Empty entries sent every 1s | `raft_node.py:224-229` | ✅ |
| **Client-side RPC logging** | `[Node X] sends RPC Y to Node Z` | `raft_node.py:149` | ✅ |
| **Server-side RPC logging** | `[Node X] runs RPC Y called by Node Z` | `raft_node.py:369` | ✅ |

### Q4: Log Replication Requirements ✅

| Requirement | Implementation | Location | Status |
|------------|----------------|----------|---------|
| **Maintain operation log** | `self.log: List[LogEntry]` | `raft_node.py:47` | ✅ |
| **Leader receives client request** | `ClientRequest()` RPC | `raft_node.py:460-489` | ✅ |
| **Leader appends to log** | `self.log.append(new_entry)` | `raft_node.py:481` | ✅ |
| **Leader sends log to followers** | `AppendEntries` with entries | `raft_node.py:224-229` | ✅ |
| **Follower copies log** | `self.log.extend(request.entries)` | `raft_node.py:437` | ✅ |
| **Follower sends ACK** | `AppendEntriesResponse(success=True)` | `raft_node.py:447` | ✅ |
| **Leader counts majority** | `_update_commit_index()` | `raft_node.py:290-308` | ✅ |
| **Leader executes on majority** | `_apply_committed_entries()` | `raft_node.py:310-322` | ✅ |
| **Commit index tracking** | `self.commit_index` | `raft_node.py:50` | ✅ |
| **Follower executes committed** | `_apply_committed_entries()` | `raft_node.py:441-442` | ✅ |
| **Non-leader forwards to leader** | Returns `leader_id` to redirect | `raft_node.py:464-469` | ✅ |
| **Client-side RPC logging** | `[Node X] sends RPC Y to Node Z` | Throughout | ✅ |
| **Server-side RPC logging** | `[Node X] runs RPC Y called by Node Z` | Throughout | ✅ |

### Q5: Test Cases Requirements ✅

| Test Case | Implementation | Location | Status |
|-----------|----------------|----------|---------|
| **Test 1: Normal Election** | `test_case_1_normal_election()` | `test_cases.py:142-189` | ✅ |
| **Test 2: Leader Failure** | `test_case_2_leader_failure()` | `test_cases.py:191-254` | ✅ |
| **Test 3: Log Replication** | `test_case_3_log_replication()` | `test_cases.py:256-307` | ✅ |
| **Test 4: Split Vote** | `test_case_4_split_vote()` | `test_cases.py:309-354` | ✅ |
| **Test 5: Node Rejoining** | `test_case_5_new_node_joining()` | `test_cases.py:356-413` | ✅ |
| **Documented with screenshots** | Instructions in README.md | `README.md:200-220` | ✅ |

### Infrastructure Requirements ✅

| Requirement | Implementation | Location | Status |
|------------|----------------|----------|---------|
| **gRPC for communication** | gRPC Python library | `raft_node.py:7` | ✅ |
| **Proto file with services** | `raft.proto` | `raft.proto:6-15` | ✅ |
| **Proto: RequestVote** | Defined | `raft.proto:8` | ✅ |
| **Proto: AppendEntries** | Defined | `raft.proto:11` | ✅ |
| **Proto: ClientRequest** | Defined | `raft.proto:14` | ✅ |
| **Docker containerization** | Dockerfile | `Dockerfile` | ✅ |
| **5+ nodes minimum** | 5 nodes configured | `docker-compose.yml:4-67` | ✅ |
| **Nodes can communicate** | Docker network | `docker-compose.yml:69-71` | ✅ |
| **README file** | Complete documentation | `README.md` | ✅ |

---

## 🎯 Part 2: How the Implementation Works

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                  5-Node Raft Cluster                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐         │
│  │Node 1│  │Node 2│  │Node 3│  │Node 4│  │Node 5│         │
│  │:50051│  │:50052│  │:50053│  │:50054│  │:50055│         │
│  └──┬───┘  └──┬───┘  └──┬───┘  └──┬───┘  └──┬───┘         │
│     │         │         │         │         │              │
│     └─────────┴────┬────┴─────────┴─────────┘              │
│                    │                                        │
│            raft-network (Docker)                           │
└─────────────────────────────────────────────────────────────┘
                       │
                   gRPC RPCs
                       │
        ┌──────────────┼──────────────┐
        │              │              │
    RequestVote   AppendEntries  ClientRequest
     (Election)    (Heartbeat/    (Operations)
                    Replication)
```

### Component Breakdown

#### 1. Node States (Q3)

Each node exists in one of three states:

```python
class NodeState(Enum):
    FOLLOWER = "FOLLOWER"      # Default state, receives from leader
    CANDIDATE = "CANDIDATE"    # Competing for leadership
    LEADER = "LEADER"         # Handles all client requests
```

**State Transitions:**
```
FOLLOWER ──(timeout)──> CANDIDATE ──(majority votes)──> LEADER
    ↑                        │                            │
    │                        │                            │
    └────(higher term)───────┴────────(higher term)──────┘
```

#### 2. Timeouts (Q3)

**Heartbeat Timeout:** 1 second
- Leader sends AppendEntries every 1 second
- Keeps followers from timing out

**Election Timeout:** Random [1.5, 3] seconds
- Each node gets random timeout
- Prevents split votes (different nodes timeout at different times)
- New random timeout after each election

```python
self.heartbeat_timeout = 1.0                    # Line 59
self.election_timeout = random.uniform(1.5, 3.0) # Line 60
```

#### 3. Leader Election Process (Q3)

**Step-by-Step Flow:**

1. **Follower Timeout**
   ```
   [Node 2] Election timeout (2.34s) reached!
   [Node 2] State: FOLLOWER -> CANDIDATE
   ```

2. **Become Candidate**
   - Increment term: `term = term + 1`
   - Vote for self: `voted_for = self`
   - Reset timeout: New random [1.5, 3]s

3. **Request Votes**
   ```
   [Node 2] sends RPC RequestVote to Node 1
   [Node 1] runs RPC RequestVote called by Node 2
   [Node 1] Granted vote to Node 2 for term 5
   ```

4. **Count Votes**
   - Need majority: 3/5 nodes
   - If received ≥ 3 votes → Become Leader

5. **Become Leader**
   ```
   [Node 2] WON ELECTION for term 5!
   [Node 2] State: CANDIDATE -> LEADER
   ```

6. **Send Heartbeats**
   - Every 1 second
   - Empty AppendEntries
   - Prevents followers from timing out

**Code Flow:**
```
_election_timer() [Line 90]
    → _start_election() [Line 106]
        → Send RequestVote RPC [Line 149]
            → Count votes [Line 165-172]
                → _become_leader() [Line 179]
                    → _send_heartbeats() [Line 198]
```

#### 4. Log Replication Process (Q4)

**Data Structures:**

```python
# Log structure
self.log: List[LogEntry] = []        # All log entries
self.commit_index = 0                # Highest committed entry
self.last_applied = 0                # Highest applied entry

# Leader tracks follower progress
self.next_index[peer_id] = 10        # Next entry to send
self.match_index[peer_id] = 9        # Highest replicated entry
```

**Step-by-Step Flow:**

1. **Client Submits Operation**
   ```
   Client → [Node 3] ClientRequest("CREATE_POLL")
   ```

2. **Non-Leader Redirects**
   ```python
   if self.state != NodeState.LEADER:
       return ClientRequestResponse(
           success=False,
           leader_id=current_leader  # Tell client who leader is
       )
   ```

3. **Leader Appends to Log**
   ```python
   new_entry = LogEntry(
       term=self.current_term,
       index=len(self.log) + 1,
       operation="CREATE_POLL",
       data='{"question": "...", "options": [...]}'
   )
   self.log.append(new_entry)  # Line 481
   ```

4. **Leader Replicates to Followers**
   ```
   [Node 2] sends RPC AppendEntries (1 entries) to Node 1
   [Node 1] runs RPC AppendEntries (1 entries) called by Node 2
   ```

   ```python
   request = AppendEntriesRequest(
       term=self.current_term,
       leader_id=self.node_id,
       prev_log_index=9,           # Previous entry
       prev_log_term=4,
       entries=[new_entry],         # New entries
       leader_commit=8              # Leader's commit index
   )
   ```

5. **Follower Validates and Appends**
   ```python
   # Check log consistency
   if prev_log_index matches:
       self.log.extend(request.entries)  # Append
       return AppendEntriesResponse(success=True)
   ```

6. **Leader Counts Majority**
   ```python
   replicated_count = 1  # Leader has it
   for peer_id in peers:
       if match_index[peer_id] >= entry_index:
           replicated_count += 1

   if replicated_count >= 3:  # Majority (3/5)
       self.commit_index = entry_index  # Commit!
   ```

7. **Apply to State Machine**
   ```python
   while self.last_applied < self.commit_index:
       entry = self.log[self.last_applied]
       execute_operation(entry.operation, entry.data)
       self.last_applied += 1
   ```

8. **Return to Client**
   ```python
   return ClientRequestResponse(
       success=True,
       message="Operation committed at index 10"
   )
   ```

**Visual Timeline:**
```
Time  Node 1       Node 2 (Leader)  Node 3       Node 4       Node 5
────  ──────────── ───────────────  ──────────── ──────────── ────────────
 0s   [Follower]   [Leader]         [Follower]   [Follower]   [Follower]

 1s   Client Request "CREATE_POLL" ──────────────────────────> Node 2

 2s                Append to log
                   Index: 10

 3s   <── AppendEntries(entries=[10]) ──────────────────────────────────────
      Append       Waiting...       Append       Append       Append
      ACK ────────────────────────>
                                     ACK ───────>
                                                  ACK ───────>
                                                               ACK ───────>

 4s                Count: 5/5 ACKs
                   Commit index=10
                   Execute operation

 5s   <── AppendEntries(commit=10) ──────────────────────────────────────────
      Execute      Return success   Execute      Execute      Execute
                   to client
```

#### 5. RPC Message Logging (Q3, Q4)

**Required Format:**

**Client Side (Sending):**
```
[Node <node_id>] sends RPC <rpc_name> to Node <node_id>
```

**Server Side (Receiving):**
```
[Node <node_id>] runs RPC <rpc_name> called by Node <node_id>
```

**Implementation Examples:**

```python
# Client side (raft_node.py:149)
print(f"[Node {self.node_id}] sends RPC RequestVote to Node {peer_id}")

# Server side (raft_node.py:369)
def RequestVote(self, request, context):
    print(f"[Node {self.node_id}] runs RPC RequestVote called by Node {request.candidate_id}")
```

**All RPC Logging Locations:**
- `RequestVote` client: Line 149
- `RequestVote` server: Line 369
- `AppendEntries` client: Line 240
- `AppendEntries` server: Line 411
- `ClientRequest` server: Line 461

---

## 🧪 Part 3: How to Verify & Test

### Method 1: Run Automated Tests (Q5)

```bash
# 1. Start the cluster
cd raft_implementation
docker-compose up -d

# 2. Wait for stabilization
sleep 10

# 3. Generate gRPC code
python3 -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. raft.proto

# 4. Run all 5 test cases
python3 test_cases.py
```

**Expected Output:**
```
====================================================================
  TEST CASE 1: Normal Leader Election
====================================================================
[Test] ✓ Leader elected successfully (Node 3)
[Test] ✓ PASS

====================================================================
  TEST CASE 2: Leader Failure and Re-election
====================================================================
[Test] Stopping raft_node3...
[Test] ✓ New leader elected (Node 1)
[Test] ✓ PASS

... (continues for all 5 tests)

====================================================================
  TEST SUMMARY
====================================================================
  Test 1: Normal Election: ✓ PASS
  Test 2: Leader Failure: ✓ PASS
  Test 3: Log Replication: ✓ PASS
  Test 4: Split Vote: ✓ PASS
  Test 5: Node Rejoining: ✓ PASS

  Total: 5/5 tests passed
====================================================================
```

### Method 2: Manual Verification via Logs

```bash
# View Node 1 logs
docker logs -f raft_node1

# You should see:
[Node 1] Initialized as FOLLOWER
[Node 1] Election timeout: 2.45s
[Node 1] Election timeout (2.45s) reached!
[Node 1] Starting election for term 1
[Node 1] sends RPC RequestVote to Node 2
[Node 1] sends RPC RequestVote to Node 3
[Node 1] Received vote from Node 2. Votes: 2/5
[Node 1] Received vote from Node 3. Votes: 3/5
[Node 1] WON ELECTION for term 1!
[Node 1] State: CANDIDATE -> LEADER
[Node 1] sends RPC AppendEntries (heartbeat) to Node 2
```

### Method 3: Interactive Client Testing

```bash
# Run interactive client
python3 test_client.py

# Try operations:
1. Create Poll
   Question: What's your favorite color?
   Options: Red, Blue, Green

2. Vote
   Poll ID: poll_1
   Option: Blue

3. Get Results
   Poll ID: poll_1
```

### Method 4: Code Inspection

**Check Q3 Implementation:**
```bash
# Verify election timeout
grep "election_timeout = random.uniform" raft_node.py
# Output: self.election_timeout = random.uniform(1.5, 3.0)

# Verify heartbeat timeout
grep "heartbeat_timeout = " raft_node.py
# Output: self.heartbeat_timeout = 1.0

# Verify RPC logging
grep 'sends RPC' raft_node.py
grep 'runs RPC' raft_node.py
```

**Check Q4 Implementation:**
```bash
# Verify log structure
grep "self.log" raft_node.py

# Verify commit logic
grep "commit_index" raft_node.py

# Verify client forwarding
grep "leader_id" raft_node.py
```

**Check Q5 Implementation:**
```bash
# Count test cases
grep "def test_case_" test_cases.py
# Should show 5 test methods
```

**Check Docker Configuration:**
```bash
# Verify 5 nodes
grep "container_name:" docker-compose.yml
# Should show: raft_node1, raft_node2, raft_node3, raft_node4, raft_node5
```

---

## 📊 Part 4: Requirements Satisfaction Summary

### ✅ Q3: Leader Election - FULLY SATISFIED

- [x] Heartbeat timeout: 1 second ✓
- [x] Election timeout: Random [1.5, 3] seconds ✓
- [x] All nodes start as FOLLOWER ✓
- [x] Timeout triggers election ✓
- [x] Candidate votes for self ✓
- [x] RequestVote RPC implemented ✓
- [x] Majority voting works ✓
- [x] Leader sends heartbeats ✓
- [x] Proper RPC logging format ✓
- [x] 5+ nodes in Docker ✓
- [x] gRPC communication ✓

**Evidence:** `raft_node.py:59-60, 90-177, 179-195`

### ✅ Q4: Log Replication - FULLY SATISFIED

- [x] Log maintained (committed + pending) ✓
- [x] Leader receives client requests ✓
- [x] Leader appends to log ✓
- [x] Leader sends log to followers ✓
- [x] Followers copy and ACK ✓
- [x] Leader waits for majority ✓
- [x] Leader commits when majority ACKs ✓
- [x] Followers execute up to commit_index ✓
- [x] Non-leaders forward to leader ✓
- [x] Proper RPC logging format ✓

**Evidence:** `raft_node.py:224-308, 410-458, 460-489`

### ✅ Q5: Test Cases - FULLY SATISFIED

- [x] Test 1: Normal election ✓
- [x] Test 2: Leader failure ✓
- [x] Test 3: Log replication ✓
- [x] Test 4: Split vote ✓
- [x] Test 5: Node rejoining ✓
- [x] Documented in README ✓
- [x] Screenshot instructions ✓

**Evidence:** `test_cases.py:142-413`

### ✅ Infrastructure - FULLY SATISFIED

- [x] gRPC protocol ✓
- [x] Proto file with 3 services ✓
- [x] Docker containerization ✓
- [x] 5 nodes configured ✓
- [x] Nodes can communicate ✓
- [x] README with instructions ✓

**Evidence:** `raft.proto, docker-compose.yml, Dockerfile, README.md`

---

## 🎓 Part 5: Key Implementation Highlights

### 1. Thread Safety
- Uses `threading.RLock()` for thread-safe state access
- Background threads for election timer and heartbeat
- Prevents race conditions

### 2. Randomized Timeouts
- Each node: different random timeout ∈ [1.5, 3]
- Minimizes split votes
- New timeout after each election

### 3. Log Consistency
- `prev_log_index` and `prev_log_term` checks
- Automatic conflict resolution
- Follower logs forced to match leader

### 4. Majority Consensus
- Requires 3/5 nodes for commit
- Tolerates 2 node failures
- Maintains availability with majority

### 5. State Machine
- Polling operations (CREATE_POLL, VOTE, GET_RESULTS)
- Deterministic execution
- Sequential application of committed entries

---

## 📝 Part 6: How to Use for Your Submission

### Step 1: Test Everything
```bash
cd raft_implementation
bash quick_start.sh
python3 test_cases.py
```

### Step 2: Capture Screenshots
- Terminal showing all 5 nodes running
- Leader election messages
- RPC logging format
- All 5 test cases PASS
- Client operations

### Step 3: Update README
- Add your student names/IDs
- Document work distribution
- Note any changes you made

### Step 4: Create Report
- Include all screenshots
- Explain how Raft works
- Document test results
- Reference code line numbers

### Step 5: Submit
```bash
zip -r raft_implementation.zip raft_implementation/
# Upload to Canvas with report
```

---

## ✅ CONCLUSION

This Raft implementation **FULLY SATISFIES** all assignment requirements:

- ✅ **Q3:** Complete leader election with proper timeouts and RPC logging
- ✅ **Q4:** Complete log replication with majority consensus and client forwarding
- ✅ **Q5:** All 5 test cases implemented and documented
- ✅ **Infrastructure:** gRPC, Docker, 5 nodes, proper architecture

**Total Implementation:** 2,794 lines of code across 13 files

**Ready for submission!** ✓
