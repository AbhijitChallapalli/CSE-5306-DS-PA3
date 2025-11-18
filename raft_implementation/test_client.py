#!/usr/bin/env python3
"""
Test Client for Raft Cluster
Submits operations to the Raft cluster and handles leader redirection
"""

import grpc
import json
import sys
import time
from typing import Optional, Tuple

import raft_pb2
import raft_pb2_grpc


class RaftClient:
    """Client for interacting with Raft cluster"""

    def __init__(self, nodes: dict):
        """
        Initialize Raft client

        Args:
            nodes: Dictionary mapping node_id -> "host:port"
        """
        self.nodes = nodes
        self.current_leader = None

    def _find_leader(self) -> Optional[int]:
        """Find the current leader by trying all nodes"""
        print("\n[Client] Searching for leader...")

        for node_id, addr in self.nodes.items():
            try:
                # Try a simple operation to see if this is the leader
                with grpc.insecure_channel(addr) as channel:
                    stub = raft_pb2_grpc.RaftNodeStub(channel)

                    # Send a dummy request
                    request = raft_pb2.ClientRequestMessage(
                        operation="PING",
                        data=json.dumps({})
                    )

                    response = stub.ClientRequest(request, timeout=2.0)

                    if response.success or response.leader_id == node_id:
                        print(f"[Client] Found leader: Node {node_id}")
                        return node_id
                    elif response.leader_id > 0:
                        print(f"[Client] Node {node_id} redirected to Node {response.leader_id}")
                        return response.leader_id

            except Exception as e:
                print(f"[Client] Node {node_id} unavailable: {e}")
                continue

        print("[Client] No leader found!")
        return None

    def submit_operation(self, operation: str, data: dict, max_retries: int = 3) -> Tuple[bool, str]:
        """
        Submit an operation to the Raft cluster

        Args:
            operation: Operation type (e.g., "CREATE_POLL", "VOTE")
            data: Operation data as dictionary
            max_retries: Maximum number of retry attempts

        Returns:
            Tuple of (success, message)
        """
        for attempt in range(max_retries):
            # Find leader if we don't know it
            if self.current_leader is None:
                self.current_leader = self._find_leader()
                if self.current_leader is None:
                    time.sleep(1)
                    continue

            # Try to submit to current leader
            try:
                addr = self.nodes[self.current_leader]
                print(f"\n[Client] Submitting operation '{operation}' to Node {self.current_leader}")

                with grpc.insecure_channel(addr) as channel:
                    stub = raft_pb2_grpc.RaftNodeStub(channel)

                    request = raft_pb2.ClientRequestMessage(
                        operation=operation,
                        data=json.dumps(data)
                    )

                    response = stub.ClientRequest(request, timeout=10.0)

                    if response.success:
                        print(f"[Client] ✓ Success: {response.message}")
                        return True, response.message
                    else:
                        # Leader changed, update and retry
                        if response.leader_id > 0:
                            print(f"[Client] Redirected to Node {response.leader_id}")
                            self.current_leader = response.leader_id
                        else:
                            print(f"[Client] ✗ Failed: {response.message}")
                            self.current_leader = None

            except Exception as e:
                print(f"[Client] Error contacting Node {self.current_leader}: {e}")
                self.current_leader = None

            # Wait before retry
            if attempt < max_retries - 1:
                print(f"[Client] Retrying... (attempt {attempt + 2}/{max_retries})")
                time.sleep(1)

        return False, "Failed to submit operation after retries"

    def create_poll(self, question: str, options: list) -> Tuple[bool, str]:
        """Create a new poll"""
        return self.submit_operation("CREATE_POLL", {
            "question": question,
            "options": options
        })

    def vote(self, poll_id: str, option: str) -> Tuple[bool, str]:
        """Submit a vote"""
        return self.submit_operation("VOTE", {
            "poll_id": poll_id,
            "option": option
        })

    def get_results(self, poll_id: str) -> Tuple[bool, str]:
        """Get poll results"""
        return self.submit_operation("GET_RESULTS", {
            "poll_id": poll_id
        })


def interactive_mode(client: RaftClient):
    """Interactive mode for testing"""
    print("\n" + "="*60)
    print("Raft Test Client - Interactive Mode")
    print("="*60)
    print("\nCommands:")
    print("  1 - Create Poll")
    print("  2 - Vote on Poll")
    print("  3 - Get Poll Results")
    print("  4 - Find Leader")
    print("  q - Quit")
    print()

    while True:
        try:
            choice = input("\nEnter command: ").strip()

            if choice == '1':
                question = input("Poll question: ")
                options_str = input("Options (comma-separated): ")
                options = [opt.strip() for opt in options_str.split(',')]

                success, msg = client.create_poll(question, options)
                print(f"\nResult: {msg}")

            elif choice == '2':
                poll_id = input("Poll ID: ")
                option = input("Option: ")

                success, msg = client.vote(poll_id, option)
                print(f"\nResult: {msg}")

            elif choice == '3':
                poll_id = input("Poll ID: ")

                success, msg = client.get_results(poll_id)
                print(f"\nResult: {msg}")

            elif choice == '4':
                leader = client._find_leader()
                if leader:
                    print(f"\nCurrent leader: Node {leader}")
                else:
                    print("\nNo leader found")

            elif choice.lower() == 'q':
                print("Goodbye!")
                break

            else:
                print("Invalid command")

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")


def run_test_scenario():
    """Run automated test scenario"""
    # Docker configuration
    nodes = {
        1: "localhost:50051",
        2: "localhost:50052",
        3: "localhost:50053",
        4: "localhost:50054",
        5: "localhost:50055"
    }

    client = RaftClient(nodes)

    print("\n" + "="*60)
    print("Running Automated Test Scenario")
    print("="*60)

    # Wait for cluster to stabilize
    print("\n[Test] Waiting for cluster to stabilize (5 seconds)...")
    time.sleep(5)

    # Test 1: Create a poll
    print("\n[Test 1] Creating a poll...")
    success, msg = client.create_poll(
        "What's your favorite programming language?",
        ["Python", "JavaScript", "Go", "Rust"]
    )
    print(f"Result: {'✓ PASS' if success else '✗ FAIL'} - {msg}")

    time.sleep(2)

    # Test 2: Submit votes
    print("\n[Test 2] Submitting votes...")
    for option in ["Python", "Python", "JavaScript", "Go", "Python"]:
        success, msg = client.vote("poll_1", option)
        print(f"  Vote for {option}: {'✓' if success else '✗'}")
        time.sleep(0.5)

    time.sleep(2)

    # Test 3: Get results
    print("\n[Test 3] Getting poll results...")
    success, msg = client.get_results("poll_1")
    print(f"Result: {'✓ PASS' if success else '✗ FAIL'} - {msg}")

    time.sleep(2)

    # Test 4: Create another poll
    print("\n[Test 4] Creating another poll...")
    success, msg = client.create_poll(
        "Best distributed consensus algorithm?",
        ["Paxos", "Raft", "2PC", "Byzantine Fault Tolerance"]
    )
    print(f"Result: {'✓ PASS' if success else '✗ FAIL'} - {msg}")

    print("\n" + "="*60)
    print("Test Scenario Complete!")
    print("="*60)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--auto":
        run_test_scenario()
    else:
        # Docker configuration
        nodes = {
            1: "localhost:50051",
            2: "localhost:50052",
            3: "localhost:50053",
            4: "localhost:50054",
            5: "localhost:50055"
        }

        client = RaftClient(nodes)
        interactive_mode(client)
