
#!/usr/bin/env python3
"""
datagram_feeder.py
------------------
Generates dummy datagram arrivals for a router simulation.

Each datagram line has the following fields:
<arrival_time_ms> <flow_id> <priority> <size_bytes> <payload>

Example output line:
12.0 2 1 512 DATA_42

Usage:
    python3 datagram_feeder.py --rate 10 --burst 4 --flows 3 --duration 5 --policy random

Options:
    --rate        Average datagram rate per second (default: 10)
    --burst       Number of datagrams per burst (default: 1)
    --flows       Number of flows (default: 1)
    --duration    Duration of simulation in seconds (default: 5)
    --policy      How priorities are assigned: [random|by_flow|uniform]
    --seed        Random seed (optional)
"""

import argparse
import random
import sys
import time

def main():
    parser = argparse.ArgumentParser(description="Datagram generator for router simulation.")
    parser.add_argument("--rate", type=float, default=10.0, help="Average datagram rate per second")
    parser.add_argument("--burst", type=int, default=1, help="Number of datagrams per burst")
    parser.add_argument("--flows", type=int, default=1, help="Number of flows")
    parser.add_argument("--duration", type=float, default=5.0, help="Simulation duration in seconds")
    parser.add_argument("--policy", type=str, choices=["random", "by_flow", "uniform"], default="random",
                        help="Priority assignment policy")
    parser.add_argument("--seed", type=int, help="Random seed for reproducibility")
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    total_packets = int(args.rate * args.duration)
    inter_arrival_time = 1.0 / args.rate  # seconds

    start_time = time.time()
    current_time = 0.0
    packet_id = 0

    while current_time < args.duration:
        for _ in range(args.burst):
            packet_id += 1
            flow_id = random.randint(1, args.flows)

            # Determine priority
            if args.policy == "random":
                priority = random.randint(0, 3)
            elif args.policy == "by_flow":
                priority = (flow_id - 1) % 4
            else:  # uniform
                priority = 1

            size = random.choice([256, 512, 1024, 1500])
            payload = f"DATA_{packet_id}"

            # Output format: arrival_time_ms flow_id priority size payload
            print(f"{current_time*1000:.1f} {flow_id} {priority} {size} {payload}")
            sys.stdout.flush()

        # Sleep to simulate real-time pacing
        time.sleep(inter_arrival_time)
        current_time = time.time() - start_time

    # Print end marker (optional)
    print("# END")
    sys.stdout.flush()

if __name__ == "__main__":
    main()
