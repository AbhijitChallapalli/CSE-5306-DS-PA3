# microservice_based/alarm_dist_sys/accounts/accounts_vote.py

import grpc
from concurrent import futures
import time

import alarm_pb2
import alarm_pb2_grpc

NODE_ID = "accounts"
PHASE_VOTE = "Voting"
PHASE_DECISION = "Decision"


class AccountsVotePhaseServicer(alarm_pb2_grpc.VotePhaseServicer):
    def __init__(self):
        self.decision_stub = alarm_pb2_grpc.DecisionPhaseStub(
            grpc.insecure_channel("localhost:61053")
        )

    def VoteOnAddAlarm(self, request, context):
        tx_id = request.tx_id
        alarm = request.alarm

        print(
            f"Phase {PHASE_VOTE} of Node {NODE_ID} "
            f"sends RPC VoteOnAddAlarm to Phase {PHASE_VOTE} of Node {NODE_ID}"
        )

        # Example: here you could verify user exists, quota, etc.
        vote = alarm_pb2.Vote.VOTE_COMMIT
        reason = "Accounts ready"

        prepared = alarm_pb2.PreparedAlarm(tx_id=tx_id, alarm=alarm)

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
    alarm_pb2_grpc.add_VotePhaseServicer_to_server(AccountsVotePhaseServicer(), server)
    server.add_insecure_port("[::]:60053")
    print("Accounts VotePhase listening on port 60053")
    server.start()
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == "__main__":
    serve()
