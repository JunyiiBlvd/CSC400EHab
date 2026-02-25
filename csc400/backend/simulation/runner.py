"""
This module provides a command-line interface to run the thermal simulation.
"""
import argparse
import csv
import sys
import time
from typing import List, Dict, Any

from .thermal_model import ThermalModel
from .node import VirtualNode


def run_simulation(duration: int, seed: int = None, output_file: str = None):
    """
    Runs the thermal simulation for a single node.

    Args:
        duration (int): The number of seconds (steps) to run the simulation.
        seed (int, optional): A random seed for deterministic runs.
        output_file (str, optional): Path to a CSV file to save the results.
    """
    # Instantiate ThermalModel with reasonable defaults
    thermal_model = ThermalModel(
        air_mass=50.0,
        heat_capacity=1005.0,
        heat_coefficient=500.0,
        cooling_coefficient=300.0,
        initial_temperature=21.0,
        ambient_temperature=20.0,
    )

    # Create a single VirtualNode
    node = VirtualNode(
        node_id="node-1",
        thermal_model=thermal_model,
        random_seed=seed
    )

    telemetry_data: List[Dict[str, Any]] = []

    # Run simulation for the specified duration
    for _ in range(duration):
        telemetry = node.step()
        telemetry_data.append(telemetry)
        time.sleep(1) # Simulate 1-second time steps

    # Output results
    if output_file:
        try:
            with open(output_file, "w", newline="") as f:
                if not telemetry_data:
                    return
                writer = csv.DictWriter(f, fieldnames=telemetry_data[0].keys())
                writer.writeheader()
                writer.writerows(telemetry_data)
            print(f"Successfully wrote {len(telemetry_data)} rows to {output_file}")
        except IOError as e:
            print(f"Error writing to file {output_file}: {e}", file=sys.stderr)
    else:
        for row in telemetry_data:
            print(row)


def main():
    """The main entry point for the CLI runner."""
    parser = argparse.ArgumentParser(
        description="Run the E-Habitat thermal simulation."
    )
    parser.add_argument(
        "--duration",
        type=int,
        required=True,
        help="Duration of the simulation in seconds.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        help="Optional random seed for deterministic runs.",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Optional path to a CSV file to save the telemetry data.",
    )
    args = parser.parse_args()

    run_simulation(duration=args.duration, seed=args.seed, output_file=args.output)


if __name__ == "__main__":
    main()
