"""
This module provides a command-line interface to run the thermal simulation.
"""
import argparse
import csv
import sys
import os
import random
from typing import List, Dict, Any

from .thermal_model import ThermalModel
from .airflow import AirflowModel
from .humidity import HumidityModel
from .node import VirtualNode


def run_simulation(duration: int, seed: int = None, output_file: str = None, fast_mode: bool = False):
    """
    Runs the thermal simulation for a single node.

    Args:
        duration (int): The number of seconds (steps) to run the simulation.
        seed (int, optional): A random seed for deterministic runs.
        output_file (str, optional): Path to a CSV file to save the results.
        fast_mode (bool): If True, skips time.sleep(1).
    """
    # Use different seeds for different components if a base seed is provided
    # to avoid identical noise sequences
    if seed is not None:
        thermal_seed = seed
        airflow_seed = seed + 1000
        humidity_seed = seed + 2000
        node_seed = seed + 3000
    else:
        thermal_seed = airflow_seed = humidity_seed = node_seed = None

    # Instantiate Models with reasonable defaults
    thermal_model = ThermalModel(
        air_mass=50.0,
        heat_capacity=1005.0,
        heat_coefficient=500.0,
        cooling_coefficient=300.0,
        initial_temperature=21.0,
        ambient_temperature=20.0,
    )
    
    airflow_model = AirflowModel(
        nominal_flow=2.5,
        random_seed=airflow_seed
    )
    
    humidity_model = HumidityModel(
        initial_humidity=45.0,
        drift=0.01,
        noise_amplitude=0.2,
        random_seed=humidity_seed,
        reference_temp=21.0
    )

    # Create a single VirtualNode
    node = VirtualNode(
        node_id="node-1",
        thermal_model=thermal_model,
        airflow_model=airflow_model,
        humidity_model=humidity_model,
        random_seed=node_seed
    )

    telemetry_data: List[Dict[str, Any]] = []

    # Run simulation for the specified duration
    print(f"Running simulation for {duration} steps...")
    for i in range(duration):
        telemetry = node.step()
        telemetry_data.append(telemetry)
        
        if (i + 1) % 10000 == 0:
            print(f"Progress: {i + 1}/{duration} steps completed.")

    # Output results
    if output_file:
        try:
            # Ensure directory exists
            if os.path.dirname(output_file):
                os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, "w", newline="") as f:
                if not telemetry_data:
                    return
                writer = csv.DictWriter(f, fieldnames=telemetry_data[0].keys())
                writer.writeheader()
                writer.writerows(telemetry_data)
            print(f"Successfully wrote {len(telemetry_data)} rows to {output_file}")
        except Exception as e:
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
