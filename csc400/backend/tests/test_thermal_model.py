"""
Unit tests for the ThermalModel class.
"""
import pytest
import random
from backend.simulation.thermal_model import ThermalModel
from backend.simulation.node import VirtualNode

# A tolerance for floating point comparisons
TOL = 1e-6

@pytest.fixture
def default_model():
    """Returns a ThermalModel with default parameters for testing."""
    return ThermalModel(
        air_mass=50.0,
        heat_capacity=1005.0,
        heat_coefficient=500.0,
        cooling_coefficient=300.0,
        initial_temperature=21.0,
        ambient_temperature=20.0,
    )

def test_temperature_increases_with_cpu_load(default_model):
    """
    Tests if the temperature increases when cpu_load is high and cooling is low.
    """
    model = default_model
    initial_temp = model.temperature
    model.step(cpu_load=1.0)
    assert model.temperature > initial_temp

def test_temperature_decreases_when_hot(default_model):
    """
    Tests if the temperature decreases when cpu_load is zero and temp is above ambient.
    """
    model = default_model
    model.temperature = 30.0  # Start well above ambient
    initial_temp = model.temperature
    model.step(cpu_load=0.0)
    assert model.temperature < initial_temp

def test_cpu_load_clamping():
    """
    Tests that the cpu_load is correctly clamped between 0 and 1.
    """
    model = ThermalModel(
        air_mass=50, heat_capacity=1005, heat_coefficient=500,
        cooling_coefficient=300, initial_temperature=21, ambient_temperature=20
    )
    
    # Test clamping at the lower bound
    temp_at_neg_one_load = model.step(cpu_load=-1.0)
    model.temperature = 21.0 # Reset
    temp_at_zero_load = model.step(cpu_load=0.0)
    assert abs(temp_at_neg_one_load - temp_at_zero_load) < TOL

    # Test clamping at the upper bound
    model.temperature = 21.0 # Reset
    temp_at_two_load = model.step(cpu_load=2.0)
    model.temperature = 21.0 # Reset
    temp_at_one_load = model.step(cpu_load=1.0)
    assert abs(temp_at_two_load - temp_at_one_load) < TOL

def test_deterministic_output_with_seed():
    """
    Tests that providing the same seed produces the same sequence of results.
    """
    def get_run_results(seed):
        """Helper to run simulation and collect results."""
        thermal_model = ThermalModel(10, 1000, 100, 50, 20, 15)
        node = VirtualNode("test-node", thermal_model, random_seed=seed)
        results = [node.step() for _ in range(10)]
        return results

    # Run the simulation twice with the same seed
    results1 = get_run_results(seed=42)
    results2 = get_run_results(seed=42)
    
    # Run a third time with a different seed
    results3 = get_run_results(seed=123)

    # Extract temperatures and CPU loads for comparison
    temps1 = [r['temperature'] for r in results1]
    temps2 = [r['temperature'] for r in results2]
    cpu1 = [r['cpu_load'] for r in results1]
    cpu2 = [r['cpu_load'] for r in results2]
    
    # The two runs with the same seed should be identical
    assert temps1 == temps2
    assert cpu1 == cpu2

    # The run with a different seed should be different
    assert temps1 != [r['temperature'] for r in results3]
    assert cpu1 != [r['cpu_load'] for r in results3]

def test_no_temperature_change_at_equilibrium():
    """
    Tests that temperature remains constant when heat generation equals cooling.
    """
    model = ThermalModel(
        air_mass=50, heat_capacity=1005, heat_coefficient=500,
        cooling_coefficient=300, initial_temperature=21, ambient_temperature=20
    )
    # P_heat = 500 * 0.6 = 300
    # Cooling = 300 * (21-20) = 300
    # Net should be zero
    cpu_load = 0.6
    
    initial_temp = model.temperature
    model.step(cpu_load=cpu_load)
    
    assert abs(model.temperature - initial_temp) < TOL
