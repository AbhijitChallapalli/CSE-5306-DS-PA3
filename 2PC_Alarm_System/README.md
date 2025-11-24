# 2PC Alarm System – Microservice-Based Implementation

This project implements a **Two-Phase Commit (2PC)** protocol for the **“Add Alarm”** functionality in a distributed alarm system.

The system is split into multiple microservices (Python + Node.js) that communicate via **gRPC** and are orchestrated with **Docker Compose**.  
The coordinator uses 2PC to ensure that **both** participants (`scheduler`, `accounts`) commit an alarm, or **both** abort it.

## `GitHub link`: https://github.com/AbhijitChallapalli/CSE-5306-DS-PA3

## How to Run

Clone the repository using this command:

```bash
git clone https://github.com/AbhijitChallapalli/CSE-5306-DS-PA3.git
```

Change directories:

```bash
cd CSE-5306-DS-PA3

cd 2PC_Alarm_System

cd microservice_based
```

From this directory:

```bash
docker compose build
```

Run the services:

```bash
docker compose up
```

# Accessing the Web UI

1. Open a browser and go to:

   ```text
   http://localhost:8080
   ```

2. Login:

   - Valid users are defined in `alarm_dist_sys/accounts/saved_users.json`.
   - Or Use this to signup [{"username": "admin", "password": "12345"}]
   - Or signup.

3. After login:

   - `/dashboard` shows Alarms + Notifications panels.
   - “Add Alarm” form submits to `/add` which triggers 2PC via the coordinator.
   - Deleting alarms goes directly through storage (not via 2PC).

4. In the project folder:

```bash
docker compose up
```

You’ll see logs interleaved from:

- `api_gateway_MS`
- `coordinator_MS`
- `scheduler_MS`
- `accounts_MS`
- `storage_MS`
- `notification_MS`

This is why the order looks “mixed” – they’re all running **concurrently**.

# 2PC Fuctionality

- **Global commit**:
  - Add alarm with title `"test" or any other name` → watch 2PC logs and see the alarm appear on the dashboard.
- **Global abort**:
  - Add alarm with title starting `"abort"` → watch that scheduler votes abort, coordinator decides GLOBAL_ABORT, accounts/scheduler abort logically, and no alarm is stored.
  - Use `docker compose logs -f coordinator` + `scheduler` + `accounts` during the demo to clearly watch the **Voting** and **Decision** phases.

# Per-service logs

In another terminal:

```bash
# Coordinator logs
docker compose logs -f coordinator

# Scheduler logs
docker compose logs -f scheduler

# Accounts logs
docker compose logs -f accounts

# Storage logs
docker compose logs -f storage

# API gateway logs
docker compose logs -f api_gateway
```

Use `Ctrl + C` to stop

Stop the docker containers

```bash
docker compose down
```

## Architecture Overview

### Microservices

- **API Gateway (`api_gateway`)**

  - Tech: Python, FastAPI, Uvicorn
  - Port: `8080`
  - Responsibilities:
    - Web UI (login, dashboard, add alarm, delete alarm)
    - Talks to:
      - `storage` (list/delete alarms)
      - `coordinator` (initiate 2PC for AddAlarm)

- **Coordinator (`coordinator`)**

  - Tech: Python, gRPC
  - Port: `60050`
  - RPC:
    - `AddAlarm2PC(AddAlarmRequest) -> Ack`
  - Responsibilities:
    - 2PC **coordinator** for AddAlarm
    - Phase 1 (Voting): calls `VoteOnAddAlarm` on `scheduler` and `accounts`
    - Phase 2 (Decision): sends global decision to `DecideOnAddAlarm` on both participants

- **Scheduler**

  - Tech:
    - `scheduler_vote.py` (Python gRPC server – VotePhase) – port `60052`
    - `scheduler_decision.js` (Node.js gRPC server – DecisionPhase) – port `61052`
    - (Existing scheduler service on `50052` for scheduling behavior)
  - Responsibilities:
    - **VotePhase**: validates and “prepares” the alarm
    - **DecisionPhase**: on **commit**, calls underlying `Scheduler.ScheduleAlarm` and indirectly causes the alarm to be stored in `storage`
    - On **abort**, drops prepared data

- **Accounts**

  - Tech:
    - `accounts_vote.py` (Python gRPC server – VotePhase) – port `60053`
    - `accounts_decision.js` (Node.js gRPC server – DecisionPhase) – port `61053`
  - Responsibilities:
    - **VotePhase**: checks logical readiness (e.g. user/account metadata) and prepares alarm
    - **DecisionPhase**: logically commits or aborts the alarm

- **Storage (`storage`)**

  - Tech: Python gRPC server
  - Port: `50051`
  - File: `storage.py`
  - Data file: `saved_alarm.json` (mounted as a Docker volume)
  - Responsibilities:
    - Persistent storage of alarms
    - RPCs like `AddAlarm`, `ListAlarms`, `DeleteAlarm`

- **Notification (`notification`)**
  - Tech: Python gRPC server
  - Port: (internal; used by scheduler)
  - Responsibilities:
    - Notifying when alarms trigger (not directly involved in 2PC for AddAlarm)

---

## Two-Phase Commit Design

### Participants

- **Coordinator**
  - Node ID: `"coordinator"`
- **Scheduler participant**
  - VotePhase: `scheduler:60052`
  - DecisionPhase: `scheduler:61052`
- **Accounts participant**
  - VotePhase: `accounts:60053`
  - DecisionPhase: `accounts:61053`

### Phase 1: Voting

1. API Gateway creates an `Alarm` from user input and calls:
   ```python
   ack = coordinator_stub.AddAlarm2PC(two_pc_req)
   ```
2. Coordinator logs:
   ```text
   [Coordinator] Starting 2PC AddAlarm, tx_id=..., user=..., title=...
   Phase Voting of Node coordinator sends RPC VoteOnAddAlarm to Phase Voting of Node scheduler
   Phase Voting of Node coordinator sends RPC VoteOnAddAlarm to Phase Voting of Node accounts
   ```
3. Each participant’s VotePhase:

   - `scheduler_vote.py`:
     - For demo: if `title` starts with `"abort"`, it **votes ABORT**:
       ```python
       if alarm.title.strip().lower().startswith("abort"):
           vote = alarm_pb2.Vote.VOTE_ABORT
           reason = "Demo rule: scheduler vetoed title starting with 'abort'"
       ```
     - Otherwise, it sends `AddPreparedAlarm` to its own DecisionPhase (Node.js) and typically votes COMMIT.
   - `accounts_vote.py`:
     - Sends `AddPreparedAlarm` to its own DecisionPhase and votes COMMIT if prepared successfully.

4. Coordinator collects votes and logs:
   ```text
   [Coordinator] Vote from scheduler: vote=0, reason=Scheduler ready
   [Coordinator] Vote from accounts: vote=0, reason=Accounts ready
   [Coordinator] Voting phase complete for tx_id=..., decision=GLOBAL_COMMIT
   ```
   or (for abort):
   ```text
   [Coordinator] Vote from scheduler: vote=1, reason=Demo rule: scheduler vetoed title starting with 'abort'
   [Coordinator] Voting phase complete for tx_id=..., decision=GLOBAL_ABORT
   ```

### Phase 2: Decision

1. If **all** votes are COMMIT → `GLOBAL_COMMIT`, else → `GLOBAL_ABORT`.
2. Coordinator sends `DecideOnAddAlarm` to each participant’s DecisionPhase:
   ```text
   Phase Decision of Node coordinator sends RPC DecideOnAddAlarm to Phase Decision of Node scheduler
   Phase Decision of Node coordinator sends RPC DecideOnAddAlarm to Phase Decision of Node accounts
   ```
3. Scheduler DecisionPhase (`scheduler_decision.js`):

   - If decision is COMMIT:
     - Calls underlying `Scheduler.ScheduleAlarm` (gRPC to local scheduler).
     - On success, replies:
       ```text
       [Scheduler DecisionPhase] COMMIT: calling Scheduler.ScheduleAlarm for tx_id=...
       ```
   - If decision is ABORT:
     - Drops prepared state:
       ```text
       [Scheduler DecisionPhase] ABORT: dropping prepared alarm for tx_id=...
       ```

4. Accounts DecisionPhase (`accounts_decision.js`):

   - If COMMIT:
     ```text
     [Accounts DecisionPhase] COMMIT: logically committing alarm for tx_id=...
     ```
   - If ABORT:
     ```text
     [Accounts DecisionPhase] ABORT: logically aborting alarm for tx_id=...
     ```

5. Coordinator logs final acks and decision:

   ```text
   [Coordinator] Decision ack from scheduler: success=True, msg=Scheduler committed alarm
   [Coordinator] Decision ack from accounts: success=True, msg=Accounts committed alarm
   [Coordinator] Decision phase complete for tx_id=..., all_ok=True, msg=Global-commit
   ```

   For abort scenario:

   ```text
   [Coordinator] Decision ack from scheduler: success=True, msg=Scheduler aborted alarm (global abort)
   [Coordinator] Decision ack from accounts: success=True, msg=Accounts logically aborted alarm (global abort)
   [Coordinator] Decision phase complete for tx_id=..., all_ok=False, msg=Global-abort
   ```

6. API Gateway prints the overall 2PC result:
   ```text
   [API] 2PC result: success=True, message=Global-commit
   ```
   or:
   ```text
   [API] 2PC result: success=False, message=Global-abort
   ```

---

## Prerequisites

- **Docker** and **Docker Compose** installed.
- Ports available:
  - `8080` – API Gateway
  - `50051` – Storage
  - `50052` – Scheduler
  - `50053` – Accounts
  - `60050` – Coordinator
  - `60052`, `60053`, `61052`, `61053` – Vote/Decision phases

---

### What to Look For

#### 1. Normal Global Commit (title not starting with "abort")

Expected flow:

1. User adds alarm (e.g., title `"test"`).
2. Logs:

   - **Coordinator**:

     ```text
     [Coordinator] Starting 2PC AddAlarm, tx_id=..., user=admin, title=test
     Phase Voting of Node coordinator sends RPC VoteOnAddAlarm to Phase Voting of Node scheduler
     Phase Voting of Node coordinator sends RPC VoteOnAddAlarm to Phase Voting of Node accounts
     [Coordinator] Vote from scheduler: vote=0, reason=Scheduler ready
     [Coordinator] Vote from accounts: vote=0, reason=Accounts ready
     [Coordinator] Voting phase complete for tx_id=..., decision=GLOBAL_COMMIT
     Phase Decision of Node coordinator sends RPC DecideOnAddAlarm to Phase Decision of Node scheduler
     Phase Decision of Node coordinator sends RPC DecideOnAddAlarm to Phase Decision of Node accounts
     [Coordinator] Decision ack from scheduler: success=True, msg=Scheduler committed alarm
     [Coordinator] Decision ack from accounts: success=True, msg=Accounts committed alarm
     [Coordinator] Decision phase complete for tx_id=..., all_ok=True, msg=Global-commit
     ```

   - **Scheduler DecisionPhase (Node)**:

     ```text
     Phase Decision of Node scheduler sends RPC AddPreparedAlarm to Phase Decision of Node scheduler
     Phase Decision of Node scheduler sends RPC DecideOnAddAlarm to Phase Decision of Node scheduler
     [Scheduler DecisionPhase] COMMIT: calling Scheduler.ScheduleAlarm for tx_id=...
     ```

   - **Accounts DecisionPhase (Node)**:

     ```text
     Phase Decision of Node accounts sends RPC AddPreparedAlarm to Phase Decision of Node accounts
     Phase Decision of Node accounts sends RPC DecideOnAddAlarm to Phase Decision of Node accounts
     [Accounts DecisionPhase] COMMIT: logically committing alarm for tx_id=...
     ```

   - **Storage**:

     ```text
     Alarm Added in Storage
     ```

   - **API Gateway**:
     ```text
     [API] 2PC result: success=True, message=Global-commit
     ```

3. The new alarm appears on `http://localhost:8080/dashboard` under the alarms list.

#### 2. Global Abort Demo (title starts with "abort")

1. User adds alarm with title `"abort test"` or `"Abort something"`.
2. Logs:

   - **Coordinator**:

     ```text
     [Coordinator] Starting 2PC AddAlarm, tx_id=..., user=admin, title=abort test
     Phase Voting of Node coordinator sends RPC VoteOnAddAlarm to Phase Voting of Node scheduler
     [Coordinator] Vote from scheduler: vote=1, reason=Demo rule: scheduler vetoed title starting with 'abort'
     [Coordinator] Voting phase complete for tx_id=..., decision=GLOBAL_ABORT
     Phase Decision of Node coordinator sends RPC DecideOnAddAlarm to Phase Decision of Node scheduler
     Phase Decision of Node coordinator sends RPC DecideOnAddAlarm to Phase Decision of Node accounts
     [Coordinator] Decision ack from scheduler: success=True, msg=Scheduler aborted alarm (global abort)
     [Coordinator] Decision ack from accounts: success=True, msg=Accounts logically aborted alarm (global abort)
     [Coordinator] Decision phase complete for tx_id=..., all_ok=False, msg=Global-abort
     ```

   - **Scheduler DecisionPhase**:

     ```text
     [Scheduler DecisionPhase] ABORT: dropping prepared alarm for tx_id=...
     ```

   - **Accounts DecisionPhase**:

     ```text
     [Accounts DecisionPhase] ABORT: logically aborting alarm for tx_id=...
     ```

   - **API Gateway**:
     ```text
     [API] 2PC result: success=False, message=Global-abort
     ```

3. **Storage** does **not** log an “Alarm Added in Storage”, and no alarm appears in the dashboard for that transaction.

---

## Persistence

- Alarms are stored in `saved_alarm.json`, which is mounted into the `storage` container:
  ```yaml
  volumes:
    - ./alarm_dist_sys/storage/saved_alarm.json:/app/saved_alarm.json
  ```
- This means alarms survive container restarts as long as the JSON file remains.

## Unusual / Important Notes for the TA

- 2PC is only applied to the Add Alarm operation. Delete/Listing follow the original single-service paths.

- The "title starts with 'abort'" rule in scheduler_vote.py is intentional and exists purely to demonstrate a GLOBAL_ABORT path and generate clean logs for the report.

- Logs from all containers appear interleaved when running docker compose up; this is expected because all microservices run concurrently.

- The VotePhase and DecisionPhase for both scheduler and accounts are split into separate Python and Node.js services, which makes the message flow more explicit in the logs.

## Contributions
- Srinivasa Sai Abhijit Challapalli - 1002059486 - Implemented the entire 2PC Algorithm, along with README and report (Q1, Q2)
- Namburi Chaitanya Krishna - 1002232417 - Implemented RAFT Algorithm along with the test cases, along with README and report (Q3, Q4, Q5)

## References:
- Distributed Alarm Systems GitHub - https://github.com/hoaihdinh/Distributed-Alarm-System/
- Distributed Voting System GitHub - https://github.com/CSE-5306-004-DISTRIBUTED-SYSTEMS/
