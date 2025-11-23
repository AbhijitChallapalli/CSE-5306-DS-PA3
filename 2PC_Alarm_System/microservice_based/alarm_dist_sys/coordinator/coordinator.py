# microservice_based/alarm_dist_sys/coordinator/coordinator.py

import grpc
from concurrent import futures
import uuid
import time

import alarm_pb2
import alarm_pb2_grpc

NODE_ID = "coordinator"
PHASE_VOTE = "Voting"
PHASE_DECISION = "Decision"

# Participants in 2PC (scheduler & accounts)
PARTICIPANTS = [
    {"node_id": "scheduler", "vote_addr": "scheduler:60052", "decision_addr": "scheduler:61052"},
    {"node_id": "accounts",  "vote_addr": "accounts:60053",  "decision_addr": "accounts:61053"},
]


class TwoPCCoordinatorServicer(alarm_pb2_grpc.TwoPCCoordinatorServicer):
    def AddAlarm2PC(self, request, context):
        alarm = request.alarm
        tx_id_str = str(uuid.uuid4())
        tx_id = alarm_pb2.TransactionId(id=tx_id_str)

        print(f"[Coordinator] Starting 2PC AddAlarm, tx_id={tx_id_str}, user={alarm.user}, title={alarm.title}")

        # ---------- Phase 1: Voting ----------
        vote_results = []
        for p in PARTICIPANTS:
            node_id = p["node_id"]
            addr = p["vote_addr"]
            channel = grpc.insecure_channel(addr)
            stub = alarm_pb2_grpc.VotePhaseStub(channel)

            vote_req = alarm_pb2.VoteRequest(
                tx_id=tx_id,
                alarm=alarm,
                **{"from": alarm_pb2.NodeInfo(node_id=NODE_ID)},
            )

            # Client-side log (required format)
            print(
                f"Phase {PHASE_VOTE} of Node {NODE_ID} "
                f"sends RPC VoteOnAddAlarm to Phase {PHASE_VOTE} of Node {node_id}"
            )

            try:
                resp = stub.VoteOnAddAlarm(vote_req, timeout=3.0)
                vote_results.append((node_id, resp))
            except Exception as e:
                print(f"[Coordinator] VoteOnAddAlarm to {node_id} failed: {e}")
                abort_resp = alarm_pb2.VoteResponse(
                    tx_id=tx_id,
                    vote=alarm_pb2.Vote.VOTE_ABORT,
                    reason="RPC failure",
                    **{"from": alarm_pb2.NodeInfo(node_id=node_id)},
                )
                vote_results.append((node_id, abort_resp))

        # Decide global outcome
        global_decision = alarm_pb2.GlobalDecision.GLOBAL_COMMIT
        for node_id, resp in vote_results:
            print(f"[Coordinator] Vote from {node_id}: vote={resp.vote}, reason={resp.reason}")
            if resp.vote == alarm_pb2.Vote.VOTE_ABORT:
                global_decision = alarm_pb2.GlobalDecision.GLOBAL_ABORT
                break

        decision_str = "GLOBAL_COMMIT" if global_decision == alarm_pb2.GlobalDecision.GLOBAL_COMMIT else "GLOBAL_ABORT"
        print(f"[Coordinator] Voting phase complete for tx_id={tx_id_str}, decision={decision_str}")

        # ---------- Phase 2: Decision ----------
        acks = []
        for p in PARTICIPANTS:
            node_id = p["node_id"]
            addr = p["decision_addr"]
            channel = grpc.insecure_channel(addr)
            stub = alarm_pb2_grpc.DecisionPhaseStub(channel)

            decision_req = alarm_pb2.DecisionRequest(
                tx_id=tx_id,
                decision=global_decision,
                **{"from": alarm_pb2.NodeInfo(node_id=NODE_ID)},
            )

            # Client-side log (required format)
            print(
                f"Phase {PHASE_DECISION} of Node {NODE_ID} "
                f"sends RPC DecideOnAddAlarm to Phase {PHASE_DECISION} of Node {node_id}"
            )

            try:
                ack = stub.DecideOnAddAlarm(decision_req, timeout=5.0)
                print(f"[Coordinator] Decision ack from {node_id}: success={ack.success}, msg={ack.message}")
                acks.append(ack)
            except Exception as e:
                print(f"[Coordinator] DecideOnAddAlarm to {node_id} failed: {e}")
                acks.append(
                    alarm_pb2.Ack(
                        tx_id=tx_id,
                        success=False,
                        message=f"Decision RPC failed to {node_id}",
                    )
                )

        all_ok = all(a.success for a in acks)
        msg = "Global-commit" if global_decision == alarm_pb2.GlobalDecision.GLOBAL_COMMIT else "Global-abort"

        print(f"[Coordinator] Decision phase complete for tx_id={tx_id_str}, all_ok={all_ok}, msg={msg}")

        return alarm_pb2.Ack(
            tx_id=tx_id,
            success=all_ok and global_decision == alarm_pb2.GlobalDecision.GLOBAL_COMMIT,
            message=msg,
        )


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    alarm_pb2_grpc.add_TwoPCCoordinatorServicer_to_server(TwoPCCoordinatorServicer(), server)
    server.add_insecure_port("[::]:60050")
    print("TwoPCCoordinator listening on port 60050")
    server.start()
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == "__main__":
    serve()
