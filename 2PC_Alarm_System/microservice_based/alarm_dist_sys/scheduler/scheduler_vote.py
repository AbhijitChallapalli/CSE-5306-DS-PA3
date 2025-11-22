# microservice_based/alarm_dist_sys/scheduler/scheduler_vote.py

import grpc
from concurrent import futures
import time

import alarm_pb2
import alarm_pb2_grpc

NODE_ID = "scheduler"
PHASE_VOTE = "Voting"
PHASE_DECISION = "Decision"


class SchedulerVotePhaseServicer(alarm_pb2_grpc.VotePhaseServicer):
    def __init__(self):
        # Local Node.js DecisionPhase on the same node (container)
        self.decision_stub = alarm_pb2_grpc.DecisionPhaseStub(
            grpc.insecure_channel("localhost:61052")
        )

    def VoteOnAddAlarm(self, request, context):
        tx_id = request.tx_id
        alarm = request.alarm

        # Server-side log (required)
        print(
            f"Phase {PHASE_VOTE} of Node {NODE_ID} "
            f"sends RPC VoteOnAddAlarm to Phase {PHASE_VOTE} of Node {NODE_ID}"
        )

        # ---------- DEMO ABORT RULE ----------
        # If the title starts with "abort", this participant vetoes.
        if alarm.title.strip().lower().startswith("abort"):
            vote = alarm_pb2.Vote.VOTE_ABORT
            reason = "Demo rule: scheduler vetoed title starting with 'abort'"
            return alarm_pb2.VoteResponse(
                tx_id=tx_id,
                vote=vote,
                reason=reason,
                **{"from": alarm_pb2.NodeInfo(node_id=NODE_ID)},
            )

        # ---------- NORMAL PREPARE-PHASE ----------
        vote = alarm_pb2.Vote.VOTE_COMMIT
        reason = "Scheduler ready"

        prepared = alarm_pb2.PreparedAlarm(tx_id=tx_id, alarm=alarm)

        # Client-side log for intra-node RPC
        print(
            f"Phase {PHASE_VOTE} of Node {NODE_ID} "
            f"sends RPC AddPreparedAlarm to Phase {PHASE_DECISION} of Node {NODE_ID}"
        )

        ack = self.decision_stub.AddPreparedAlarm(prepared)

        if not ack.success:
            vote = alarm_pb2.Vote.VOTE_ABORT
            reason = f"Failed to store prepared alarm: {ack.message}"

        return alarm_pb2.VoteResponse(
            tx_id=tx_id,
            vote=vote,
            reason=reason,
            **{"from": alarm_pb2.NodeInfo(node_id=NODE_ID)},
        )


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    alarm_pb2_grpc.add_VotePhaseServicer_to_server(SchedulerVotePhaseServicer(), server)
    server.add_insecure_port("[::]:60052")  # VotePhase port
    print("Scheduler VotePhase listening on port 60052")
    server.start()
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == "__main__":
    serve()

