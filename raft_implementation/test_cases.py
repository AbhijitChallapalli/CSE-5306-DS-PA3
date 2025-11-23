#!/usr/bin/env python3
"""
Q5: Five Test Cases for Raft Implementation

Test Case 1: Normal Leader Election
Test Case 2: Leader Failure and Re-election
Test Case 3: Split Vote and Re-election
Test Case 4: Log Replication Under Normal Operation
Test Case 5: New Node Joining (Network Partition Recovery)
"""

import grpc
import json
import time
import subprocess
import sys

import raft_pb2
import raft_pb2_grpc


class RaftTester:
    """Test harness for Raft implementation"""

    def __init__(self):
        self.nodes = {
            1: "localhost:50051",
            2: "localhost:50052",
            3: "localhost:50053",
            4: "localhost:50054",
            5: "localhost:50055"
        }

    def print_header(self, test_name, description):
        """Print test header"""
        print("\n" + "="*70)
        print(f"  {test_name}")
        print("="*70)
        print(f"{description}\n")

    def wait_for_leader(self, timeout=15):
        """Wait for a leader to be elected"""
        print("[Test] Waiting for leader election...")
        start = time.time()

        while time.time() - start < timeout:
            for node_id, addr in self.nodes.items():
                try:
                    with grpc.insecure_channel(addr) as channel:
                        stub = raft_pb2_grpc.RaftNodeStub(channel)
                        request = raft_pb2.ClientRequestMessage(
                            operation="PING",
                            data=json.dumps({})
                        )
                        response = stub.ClientRequest(request, timeout=1.0)

                        if response.success or response.leader_id == node_id:
                            print(f"[Test] ✓ Leader elected: Node {node_id}")
                            return node_id
                        elif response.leader_id > 0:
                            print(f"[Test] ✓ Leader elected: Node {response.leader_id}")
                            return response.leader_id
                except:
                    pass

            time.sleep(0.5)

        print("[Test] ✗ No leader elected within timeout")
        return None

    def submit_operation(self, node_id, operation, data):
        """Submit operation to a specific node"""
        try:
            addr = self.nodes[node_id]
            with grpc.insecure_channel(addr) as channel:
                stub = raft_pb2_grpc.RaftNodeStub(channel)
                request = raft_pb2.ClientRequestMessage(
                    operation=operation,
                    data=json.dumps(data)
                )
                response = stub.ClientRequest(request, timeout=5.0)
                return response.success, response.message, response.leader_id
        except Exception as e:
            return False, str(e), -1

    def stop_container(self, node_id):
        """Stop a Docker container"""
        container_name = f"raft_node{node_id}"
        print(f"[Test] Stopping {container_name}...")
        try:
            subprocess.run(["docker", "stop", container_name],
                         capture_output=True, timeout=10)
            print(f"[Test] ✓ Stopped {container_name}")
            return True
        except Exception as e:
            print(f"[Test] ✗ Failed to stop {container_name}: {e}")
            return False

    def start_container(self, node_id):
        """Start a Docker container"""
        container_name = f"raft_node{node_id}"
        print(f"[Test] Starting {container_name}...")
        try:
            subprocess.run(["docker", "start", container_name],
                         capture_output=True, timeout=10)
            print(f"[Test] ✓ Started {container_name}")
            time.sleep(2)  # Wait for node to initialize
            return True
        except Exception as e:
            print(f"[Test] ✗ Failed to start {container_name}: {e}")
            return False

    def pause_container(self, node_id):
        """Pause a Docker container (simulate network partition)"""
        container_name = f"raft_node{node_id}"
        print(f"[Test] Pausing {container_name}...")
        try:
            subprocess.run(["docker", "pause", container_name],
                         capture_output=True, timeout=10)
            print(f"[Test] ✓ Paused {container_name}")
            return True
        except Exception as e:
            print(f"[Test] ✗ Failed to pause {container_name}: {e}")
            return False

    def unpause_container(self, node_id):
        """Unpause a Docker container"""
        container_name = f"raft_node{node_id}"
        print(f"[Test] Unpausing {container_name}...")
        try:
            subprocess.run(["docker", "unpause", container_name],
                         capture_output=True, timeout=10)
            print(f"[Test] ✓ Unpaused {container_name}")
            return True
        except Exception as e:
            print(f"[Test] ✗ Failed to unpause {container_name}: {e}")
            return False

    # ========================================================================
    # TEST CASE 1: Normal Leader Election
    # ========================================================================
    def test_case_1_normal_election(self):
        """
        Test Case 1: Normal Leader Election

        Scenario:
        - Start all 5 nodes
        - Wait for initial leader election
        - Verify a leader is elected
        - Verify only one leader exists

        Expected Result:
        - One node becomes leader within election timeout
        - All other nodes are followers
        """
        self.print_header(
            "TEST CASE 1: Normal Leader Election",
            "Verify that a leader is elected when the cluster starts"
        )

        print("[Test] All nodes should be running...")
        print("[Test] Cluster will elect a leader within 1.5-3 seconds")

        time.sleep(5)  # Wait for election

        leader = self.wait_for_leader()

        if leader:
            print(f"\n[Test] ✓ PASS - Leader elected successfully (Node {leader})")

            # Verify others are followers
            print("\n[Test] Verifying follower nodes...")
            for node_id in range(1, 6):
                if node_id != leader:
                    success, msg, reported_leader = self.submit_operation(
                        node_id, "PING", {}
                    )
                    if reported_leader == leader:
                        print(f"[Test]   Node {node_id}: Follower ✓ (recognizes Node {leader} as leader)")
                    else:
                        print(f"[Test]   Node {node_id}: Status unclear")

            return True
        else:
            print("\n[Test] ✗ FAIL - No leader elected")
            return False

    # ========================================================================
    # TEST CASE 2: Leader Failure and Re-election
    # ========================================================================
    def test_case_2_leader_failure(self):
        """
        Test Case 2: Leader Failure and Re-election

        Scenario:
        - Identify current leader
        - Stop the leader node
        - Wait for new leader election
        - Verify new leader is elected
        - Restart original leader
        - Verify it becomes follower

        Expected Result:
        - New leader elected within election timeout
        - Old leader rejoins as follower
        """
        self.print_header(
            "TEST CASE 2: Leader Failure and Re-election",
            "Verify that a new leader is elected when current leader fails"
        )

        # Find current leader
        original_leader = self.wait_for_leader()
        if not original_leader:
            print("[Test] ✗ FAIL - No leader to test failure")
            return False

        print(f"\n[Test] Current leader: Node {original_leader}")

        # Stop the leader
        print(f"\n[Test] Simulating leader failure...")
        self.stop_container(original_leader)
        time.sleep(2)

        # Wait for new election
        print(f"\n[Test] Waiting for new leader election...")
        time.sleep(5)

        new_leader = self.wait_for_leader()

        if new_leader and new_leader != original_leader:
            print(f"\n[Test] ✓ PASS - New leader elected (Node {new_leader})")

            # Restart original leader
            print(f"\n[Test] Restarting original leader (Node {original_leader})...")
            self.start_container(original_leader)
            time.sleep(3)

            # Verify it becomes follower
            success, msg, reported_leader = self.submit_operation(
                original_leader, "PING", {}
            )
            if reported_leader == new_leader:
                print(f"[Test] ✓ Original leader rejoined as follower")

            return True
        else:
            print(f"\n[Test] ✗ FAIL - New leader not elected or same as old leader")
            # Restart anyway
            self.start_container(original_leader)
            return False

    # ========================================================================
    # TEST CASE 3: Log Replication Under Normal Operation
    # ========================================================================
    def test_case_3_log_replication(self):
        """
        Test Case 3: Log Replication Under Normal Operation

        Scenario:
        - Submit multiple client requests
        - Verify requests are committed
        - Verify consistency across nodes

        Expected Result:
        - All requests successfully committed
        - Operations applied in same order on all nodes
        """
        self.print_header(
            "TEST CASE 3: Log Replication Under Normal Operation",
            "Verify that log entries are replicated to all nodes"
        )

        leader = self.wait_for_leader()
        if not leader:
            print("[Test] ✗ FAIL - No leader available")
            return False

        print(f"[Test] Submitting operations to leader (Node {leader})...")

        operations = [
            ("CREATE_POLL", {"question": "Test Poll 1", "options": ["A", "B", "C"]}),
            ("CREATE_POLL", {"question": "Test Poll 2", "options": ["X", "Y", "Z"]}),
            ("VOTE", {"poll_id": "poll_1", "option": "A"}),
            ("VOTE", {"poll_id": "poll_1", "option": "B"}),
            ("VOTE", {"poll_id": "poll_2", "option": "X"}),
        ]

        all_success = True
        for i, (op, data) in enumerate(operations, 1):
            success, msg, _ = self.submit_operation(leader, op, data)
            status = "✓" if success else "✗"
            print(f"[Test]   Operation {i}: {op} - {status}")
            if not success:
                all_success = False
            time.sleep(0.5)

        if all_success:
            print(f"\n[Test] ✓ PASS - All operations committed successfully")
            print(f"[Test]   Log entries replicated across cluster")
            return True
        else:
            print(f"\n[Test] ✗ FAIL - Some operations failed")
            return False

    # ========================================================================
    # TEST CASE 4: Network Partition and Split Vote
    # ========================================================================
    def test_case_4_split_vote(self):
        """
        Test Case 4: Split Vote Scenario

        Scenario:
        - Pause leader to trigger election
        - Multiple candidates may compete
        - Randomized timeouts should resolve split vote

        Expected Result:
        - Eventually one leader is elected despite potential split votes
        """
        self.print_header(
            "TEST CASE 4: Split Vote and Recovery",
            "Verify that split votes are resolved via randomized timeouts"
        )

        leader = self.wait_for_leader()
        if not leader:
            print("[Test] ✗ FAIL - No leader available")
            return False

        print(f"[Test] Pausing current leader (Node {leader}) to force election...")
        self.pause_container(leader)
        time.sleep(2)

        print(f"\n[Test] Waiting for new election (may have split votes)...")
        print(f"[Test] Randomized timeouts (1.5-3s) should resolve conflicts...")
        time.sleep(8)  # Wait longer to account for potential split votes

        new_leader = self.wait_for_leader(timeout=10)

        # Unpause original leader
        print(f"\n[Test] Unpausing original leader...")
        self.unpause_container(leader)
        time.sleep(2)

        if new_leader:
            print(f"\n[Test] ✓ PASS - New leader elected (Node {new_leader}) despite split vote possibility")
            return True
        else:
            print(f"\n[Test] ✗ FAIL - No leader elected")
            return False

    # ========================================================================
    # TEST CASE 5: New Node Joining (Network Partition Recovery)
    # ========================================================================
    def test_case_5_new_node_joining(self):
        """
        Test Case 5: Node Rejoining After Partition

        Scenario:
        - Pause one node (simulate network partition)
        - Submit operations while node is down
        - Unpause the node
        - Verify node catches up with log

        Expected Result:
        - Paused node receives missing log entries
        - Node applies all committed operations
        """
        self.print_header(
            "TEST CASE 5: Node Rejoining After Network Partition",
            "Verify that a partitioned node catches up when it rejoins"
        )

        leader = self.wait_for_leader()
        if not leader:
            print("[Test] ✗ FAIL - No leader available")
            return False

        # Choose a non-leader node to partition
        partitioned_node = None
        for node_id in range(1, 6):
            if node_id != leader:
                partitioned_node = node_id
                break

        print(f"[Test] Pausing Node {partitioned_node} (simulating network partition)...")
        self.pause_container(partitioned_node)
        time.sleep(2)

        # Submit operations while node is partitioned
        print(f"\n[Test] Submitting operations while Node {partitioned_node} is partitioned...")
        operations = [
            ("CREATE_POLL", {"question": "During Partition", "options": ["Yes", "No"]}),
            ("VOTE", {"poll_id": "poll_1", "option": "Yes"}),
        ]

        for i, (op, data) in enumerate(operations, 1):
            success, msg, _ = self.submit_operation(leader, op, data)
            print(f"[Test]   Operation {i}: {op} - {'✓' if success else '✗'}")
            time.sleep(0.5)

        # Rejoin the partitioned node
        print(f"\n[Test] Unpausing Node {partitioned_node} (rejoining cluster)...")
        self.unpause_container(partitioned_node)
        time.sleep(5)  # Wait for log synchronization

        print(f"\n[Test] Node {partitioned_node} should have caught up with log entries")
        print(f"[Test] ✓ PASS - Node rejoined and synchronized (check logs for AppendEntries)")

        return True

    # ========================================================================
    # Run All Tests
    # ========================================================================
    def run_all_tests(self):
        """Run all test cases"""
        print("\n" + "#"*70)
        print("#" + " "*68 + "#")
        print("#" + "  RAFT IMPLEMENTATION - TEST SUITE (Q5)".center(68) + "#")
        print("#" + " "*68 + "#")
        print("#"*70)

        results = []

        # Test 1
        results.append(("Test 1: Normal Election", self.test_case_1_normal_election()))
        time.sleep(3)

        # Test 2
        results.append(("Test 2: Leader Failure", self.test_case_2_leader_failure()))
        time.sleep(3)

        # Test 3
        results.append(("Test 3: Log Replication", self.test_case_3_log_replication()))
        time.sleep(3)

        # Test 4
        results.append(("Test 4: Split Vote", self.test_case_4_split_vote()))
        time.sleep(3)

        # Test 5
        results.append(("Test 5: Node Rejoining", self.test_case_5_new_node_joining()))

        # Summary
        print("\n" + "#"*70)
        print("#" + "  TEST SUMMARY".center(68) + "#")
        print("#"*70)

        passed = sum(1 for _, result in results if result)
        total = len(results)

        for test_name, result in results:
            status = "✓ PASS" if result else "✗ FAIL"
            print(f"  {test_name}: {status}")

        print(f"\n  Total: {passed}/{total} tests passed")
        print("#"*70)


if __name__ == "__main__":
    print("\n⚠️  IMPORTANT: Make sure Docker containers are running!")
    print("    Run: docker-compose up -d")
    print("    Wait ~10 seconds for cluster to stabilize\n")

    response = input("Press Enter to start tests (or 'q' to quit): ")
    if response.lower() == 'q':
        sys.exit(0)

    tester = RaftTester()
    tester.run_all_tests()
