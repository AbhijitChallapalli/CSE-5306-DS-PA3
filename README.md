
# 2PC Alarm System – Microservice-Based Implementation

This project implements a **Two-Phase Commit (2PC)** protocol for the **“Add Alarm”** functionality in a distributed alarm system.

The system is split into multiple microservices (Python + Node.js) that communicate via **gRPC** and are orchestrated with **Docker Compose**.  
The coordinator uses 2PC to ensure that **both** participants (`scheduler`, `accounts`) commit an alarm, or **both** abort it.

> **GitHub repository:**  
> https://github.com/AbhijitChallapalli/CSE-5306-DS-PA3

---

## 1. How to Compile and Run

### 1.1. Prerequisites

- **Docker** and **Docker Compose** installed.
- The following ports available on your machine:
  - `8080` – API Gateway / Web UI
  - `50051` – Storage
  - `50052` – Scheduler
  - `50053` – Accounts
  - `60050` – 2PC Coordinator
  - `60052`, `60053`, `61052`, `61053` – Vote/Decision phases

No separate compilation step is required beyond Docker image builds. All microservices are built and run through Docker Compose.

### 1.2. Clone and Build

```bash
git clone https://github.com/AbhijitChallapalli/CSE-5306-DS-PA3.git

cd CSE-5306-DS-PA3
cd 2PC_Alarm_System
cd microservice_based

# Build all images
docker compose build
```

### 1.3. Run the Services

From the `microservice_based` directory:

```bash
docker compose up
```

This starts the following containers (names may vary slightly depending on your Compose file):

- `api_gateway_MS`
- `coordinator_MS`
- `scheduler_MS`
- `accounts_MS`
- `storage_MS`
- `notification_MS`

You can stop everything with:

```bash
docker compose down
```

---

## 2. Accessing the Web UI

1. Open a browser and go to:

   ```text
   http://localhost:8080
   ```

2. Login:

   - Valid users are defined in `alarm_dist_sys/accounts/saved_users.json`.
   - Or use this to seed a simple user:  
     `{"username": "admin", "password": "12345"}`  
     (you can also sign up via the UI).

3. After login:

   - `/dashboard` shows *Alarms* and *Notifications* panels.
   - The “Add Alarm” form submits to `/add` which triggers **2PC** via the coordinator.
   - Deleting alarms goes **directly through storage** (not via 2PC) and behaves like the original Group 16 system.

---

## 3. 2PC Functionality (What Is Being Coordinated)

We use 2PC **only** for the `Add Alarm` operation. The behavior is:

- **Global commit** (successful alarm creation):
  - Add an alarm with a normal title (e.g., `"test"` or any other name).
  - Watch the 2PC logs in `coordinator`, `scheduler`, and `accounts` and verify that the alarm appears on the dashboard.

- **Global abort** (demo rule):
  - Add an alarm with a title starting with `"abort"` (e.g., `"abort test"`).
  - The `scheduler` participant deliberately **votes ABORT** for demo purposes.
  - The coordinator decides **GLOBAL_ABORT**; both `scheduler` and `accounts` abort logically, and **no alarm is stored**.

You can see detailed 2PC logs by running:

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

Use `Ctrl + C` to stop following logs in each terminal.

---

## 4. Architecture Overview

### 4.1. Microservices

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
    - Existing scheduler service on `50052` for actual scheduling behavior
  - Responsibilities:
    - **VotePhase**: validates and “prepares” the alarm
    - **DecisionPhase**: on **commit**, calls underlying `Scheduler.ScheduleAlarm` and indirectly causes the alarm to be stored in `storage`; on **abort**, drops prepared data

- **Accounts**
  - Tech:
    - `accounts_vote.py` (Python gRPC server – VotePhase) – port `60053`
    - `accounts_decision.js` (Node.js gRPC server – DecisionPhase) – port `61053`
  - Responsibilities:
    - **VotePhase**: checks logical readiness (e.g., user/account metadata) and prepares a pending alarm
    - **DecisionPhase**: logically commits or aborts the alarm based on coordinator’s decision

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
  - Port: internal; used by scheduler  
  - Responsibilities:
    - Notifying when alarms trigger (not directly involved in 2PC for AddAlarm)

### 4.2. Persistence

Alarms are stored in `saved_alarm.json`, which is mounted into the `storage` container:

```yaml
volumes:
  - ./alarm_dist_sys/storage/saved_alarm.json:/app/saved_alarm.json
```

As long as this file is preserved, alarms survive container restarts.

---

## 5. Two-Phase Commit Design

### 5.1. Participants

- **Coordinator**
  - Node ID: `"coordinator"`
- **Scheduler participant**
  - VotePhase: `scheduler:60052`
  - DecisionPhase: `scheduler:61052`
- **Accounts participant**
  - VotePhase: `accounts:60053`
  - DecisionPhase: `accounts:61053`

### 5.2. Phase 1 – Voting

1. API Gateway creates an `Alarm` from user input and calls:
   ```python
   ack = coordinator_stub.AddAlarm2PC(two_pc_req)
   ```
2. Coordinator logs something like:
   ```text
   [Coordinator] Starting 2PC AddAlarm, tx_id=..., user=..., title=...
   Phase Voting of Node coordinator sends RPC VoteOnAddAlarm to Phase Voting of Node scheduler
   Phase Voting of Node coordinator sends RPC VoteOnAddAlarm to Phase Voting of Node accounts
   ```
3. Each participant’s VotePhase:
   - `scheduler_vote.py`:
     - If `title` starts with `"abort"`, it **votes ABORT** (demo rule).
     - Otherwise, it sends `AddPreparedAlarm` to its own DecisionPhase and votes COMMIT.
   - `accounts_vote.py`:
     - Sends `AddPreparedAlarm` to its DecisionPhase and votes COMMIT if prepared successfully.

### 5.3. Phase 2 – Decision

1. If **all** votes are COMMIT → `GLOBAL_COMMIT`, else → `GLOBAL_ABORT`.
2. Coordinator sends `DecideOnAddAlarm` to each participant’s DecisionPhase:
   ```text
   Phase Decision of Node coordinator sends RPC DecideOnAddAlarm to Phase Decision of Node scheduler
   Phase Decision of Node coordinator sends RPC DecideOnAddAlarm to Phase Decision of Node accounts
   ```
3. Scheduler DecisionPhase:
   - On COMMIT: calls `Scheduler.ScheduleAlarm` and confirms the alarm in storage.
   - On ABORT: drops any prepared state.
4. Accounts DecisionPhase:
   - On COMMIT: logically commits the alarm for the user.
   - On ABORT: discards the pending alarm.
5. Coordinator aggregates acknowledgements and returns the final status (`Global-commit` or `Global-abort`) back to the API gateway.

---

## 6. Unusual / Important Notes for the TA

- 2PC is **only** applied to the **Add Alarm** operation. Delete/Listing follow the original single-service paths.
- The `"title starts with 'abort'"` rule in `scheduler_vote.py` is **intentional** and exists purely to demonstrate a **GLOBAL_ABORT** path and generate clean logs for the report.
- Logs from all containers appear interleaved when running `docker compose up`; this is expected because all microservices run concurrently.
- The VotePhase and DecisionPhase for both `scheduler` and `accounts` are split into **separate Python and Node.js services**, which makes the message flow more explicit in the logs.

---

## 7. External Sources Referenced

Please update this section based on what you actually used while developing the project. For grading transparency, here are the placeholders:

- CSE-5306 course slides and project handout for the 2PC specification.
- Official gRPC documentation for Python and Node.js (API reference and examples).
- Official Docker and Docker Compose documentation for container orchestration.

> **Note:** If you used any additional tutorials, blog posts, GitHub repositories, or AI tools, list them here explicitly.

---

## 8. Contact

If there are any issues reproducing the results or running the containers, please check the GitHub repository’s issue tracker or contact the author via the email associated with the repository.
