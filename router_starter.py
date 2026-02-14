#!/usr/bin/env python3
"""
router.py 
------------------------
This program will simulate a simplified network-layer router that processes
incoming datagrams according to different queueing disciplines.
--------------------------------------------------------------
Input Format:
<arrival_time_ms> <flow_id> <priority> <size_bytes> <payload>

Example:
12.0 2 1 512 DATA_42

Usage:
    python3 router.py --policy fcfs
    python3 router.py --policy priority
    python3 router.py --policy rr
    python3 router.py --policy wfq --weights 3,2,1   # optional extra credit
--------------------------------------------------------------
"""

import sys
import argparse
from collections import deque, defaultdict
import heapq
import time
from typing import Any


# ---------------------------------------------------------------------
# Data structure to represent a packet
# ---------------------------------------------------------------------
class Packet:
    def __init__(self, arrival_time, flow_id, priority, size, payload):
        """Represents a single network-layer packet."""
        self.arrival_time = float(arrival_time)
        self.flow_id = int(flow_id)
        self.priority = int(priority)
        self.size = int(size)
        self.payload = payload

    def __lt__(self, other):
        #compare by priority
        if self.priority != other.priority:
            return self.priority < other.priority
        #if priority = same, then compare time
        return self.arrival_time < other.arrival_time

    def __repr__(self):
        """Readable representation of the packet."""
        return (f"Packet(flow={self.flow_id}, prio={self.priority}, "
                f"size={self.size}, payload='{self.payload}')")


# ---------------------------------------------------------------------
# Queue Manager
# ---------------------------------------------------------------------
class QueueManager:
    def __init__(self, policy="fcfs", weights=None):
        self.policy = policy
        self.weights = self.parse_weights(weights)

        # Queues used for different scheduling policies
        self.queue = deque()             # FCFS
        self.heap = []                   # Priority
        self.flow_queues = defaultdict(deque)  # RR & WFQ
        self.last_flow = None            # For RR
        self.wfq_finish_times = defaultdict(float)
        self.wfq_virtual_time = 0.0

    def parse_weights(self, weights):
        """Parse weights for WFQ (Extra Credit)."""
        if not weights:
            return {}
        w_list = [float(w) for w in weights.split(",")]
        return {i + 1: w for i, w in enumerate(w_list)}

    # -------------------------------------------------------------
    # DONE: Implement enqueue() logic for all policies
    # -------------------------------------------------------------
    def enqueue(self, pkt):
        #FCFS: simple append to queue
        if self.policy == "fcfs":
            self.queue.append(pkt)

        #Priority: heap ordered by priority
        elif self.policy == "priority":
            #push 3 things onto heap, heap keeps lowest priority on top
            heapq.heappush(self.heap, (pkt.priority, pkt.arrival_time, pkt))

        #Round-robin: add a packet to its own flow's queue
        elif self.policy == "rr":
            self.flow_queues[pkt.flow_id].append(pkt)

    # -------------------------------------------------------------
    # DONE: Implement dequeue() logic for each policy
    # -------------------------------------------------------------
    def dequeue(self):

        #remove and return first packet
        if self.policy == "fcfs":
            if self.queue:
                return self.queue.popleft()
            return None

        #pop the tuple that was on the heap, and return the packet
        elif self.policy == "priority":
            if self.heap:
                _prio, _arr_ms, pkt = heapq.heappop(self.heap)
                return pkt
            return None


        elif self.policy == "rr":
            #check to see if flow has packets
            if not any(self.flow_queues.values()):
                return None
            #store sorted list of flow ID's
            flow_ids = sorted(self.flow_queues.keys())

            #determine where to start
            start_index = 0

            #if we served from a flow previous
            if self.last_flow in flow_ids:
                #start from next flow after last
                start_index = (flow_ids.index(self.last_flow) + 1) % len(flow_ids)
            #search through all flows
            for j in range(len(flow_ids)):
                #calc actual index
                index = (start_index + j) % len(flow_ids)
                #store flow id in variable
                fid = flow_ids[index]
                #if the flow has packets waiting
                if self.flow_queues[fid]:
                    #remove first packet from the queue
                    pkt = self.flow_queues[fid].popleft()
                    #if the flow's queue is empty, remove from dictionary
                    if not self.flow_queues[fid]:
                        del self.flow_queues[fid]
                    #remeber this was the last flow served
                    self.last_flow = fid
                    return pkt
            return None
        return None

# ---------------------------------------------------------------------
# Main router simulation
# ---------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Simplified Router Simulation")
    parser.add_argument("--policy", type=str,
                        choices=["fcfs", "priority", "rr", "wfq"],
                        default="fcfs",
                        help="Queueing discipline to use.")
    parser.add_argument("--output_rate", type=float, default=10.0,
                        help="Transmission rate (packets per second)")
    parser.add_argument("--weights", type=str, default=None,
                        help="Comma-separated weights for WFQ (extra credit)")
    args = parser.parse_args()

    qm = QueueManager(policy=args.policy, weights=args.weights)

    #changed: 1.0->1000.0
    send_interval = 1000.0 / args.output_rate

    # -------------------------------------------------------------
    # DONE: Parse input datagrams and print packet info
    # -------------------------------------------------------------
    packets = []
    for line in sys.stdin:
        if not line.strip() or line.startswith("#"):
            continue
        # Parse the packet fields
        arrival_time, flow_id, priority, size, payload = line.strip().split(maxsplit=4)
        pkt = Packet(arrival_time, flow_id, priority, size, payload)
        packets.append(pkt)
        print(f"[INPUT] {pkt}")
    # -------------------------------------------------------------
    # DONE: Simulate enqueue/dequeue behavior
    # -------------------------------------------------------------
    # For now, just demonstrate basic parsing.

    #sorting packets based on arrival time
    packets.sort(key=lambda p: p.arrival_time)

    #print summary info
    print(f"\n[INFO] Parsed {len(packets)} packets.")
    print(f"[INFO] Policy selected: {args.policy}")
    print("[INFO] Router simulation ready to implement.\n")

    # index of next packet to arrive
    n = len(packets)

    #idex of next packet
    i = 0

    #current time
    now = 0.0

    #next time router can send
    next_send_time = 0.0

    #helper function to check if the queues are empty
    def queues_empty():
        if args.policy in ("fcfs",):
            return len(qm.queue) == 0
        if args.policy in ("priority"):
            return len(qm.heap) == 0
        if args.policy == "rr":
            return not any(qm.flow_queues.values())
        return True

    #main loop: pcks remain or queue not empty
    while i < n or not queues_empty():
        if i < n:
            next_arrival = packets[i].arrival_time
        else:
            next_arrival = float("inf")

        #a packet arrives before the next send moment
        if next_arrival <= next_send_time:
            #new simulation time to arrival time
            now = next_arrival
            #store arriving packet in variable
            pkt = packets[i]
            #add it to the queue
            qm.enqueue(pkt)
            #log event
            print(f"[t={now:6.1f}ms] ENQUEUE flow={pkt.flow_id} prio={pkt.priority} "
                  f"size={pkt.size} payload={pkt.payload}")
            i += 1
            continue

        # time to send
        else:  # next_send_time < next_arrival
            # new simulation time to arrival time
            now = next_send_time
            # store arriving packet in variable
            pkt = qm.dequeue()
            #if we got a packet
            if pkt is not None:
                #log event
                print(f"[t={now:6.1f}ms] SEND    flow={pkt.flow_id} prio={pkt.priority} "
                      f"size={pkt.size} payload={pkt.payload}")
                #schedule next send time
                next_send_time = now + send_interval
            #if queue was empty
            else:
                #if there are more arriving
                if next_arrival != float('inf'):
                    #jump forward 
                    next_send_time = next_arrival
                else:
                    break
    print("[INFO] Simulation complete (Week 1 base run).")
if __name__ == "__main__":
    main()
