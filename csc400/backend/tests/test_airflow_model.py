"""
Unit tests for the AirflowModel class.
"""
import pytest
from backend.simulation.airflow import AirflowModel

# A tolerance for floating point comparisons
TOL = 1e-6

@pytest.fixture
def default_airflow_model():
    """Returns an AirflowModel with default nominal flow for testing.
    Using seed 42 to make behavior deterministic for range checks.
    """
    return AirflowModel(nominal_flow=100.0, random_seed=42)

def test_no_obstruction_flow_equals_nominal(default_airflow_model):
    """
    Tests that with no obstruction, the current flow is near nominal.
    Updated to account for AR(1) noise.
    """
    model = default_airflow_model
    airflow = model.step(temperature=20.88)
    # With setpoint 20.88, hvac_response is 0. 
    # Check that it is within reasonable noise bounds.
    assert 95.0 <= airflow <= 105.0

def test_fifty_percent_obstruction_flow_is_half_nominal(default_airflow_model):
    """
    Tests that with 50% obstruction, the current flow is near half nominal.
    """
    model = default_airflow_model
    model.set_obstruction(0.5)
    airflow = model.step(temperature=20.88)
    assert 45.0 <= airflow <= 55.0

def test_full_obstruction_flow_is_zero(default_airflow_model):
    """
    Tests that with full obstruction, the current flow is zero.
    """
    model = default_airflow_model
    model.set_obstruction(1.0)
    assert abs(model.step() - 0.0) < TOL
    assert abs(model.current_flow - 0.0) < TOL

def test_obstruction_clamped_between_zero_and_one(default_airflow_model):
    """
    Tests that the obstruction ratio is correctly clamped between 0 and 1.
    """
    model = default_airflow_model

    model.set_obstruction(-0.5)
    assert abs(model.obstruction_ratio - 0.0) < TOL
    airflow = model.step(temperature=20.88)
    assert 95.0 <= airflow <= 105.0

    model.set_obstruction(1.5)
    assert abs(model.obstruction_ratio - 1.0) < TOL
    assert abs(model.step() - 0.0) < TOL

    model.set_obstruction(0.3)
    assert abs(model.obstruction_ratio - 0.3) < TOL
    airflow = model.step(temperature=20.88)
    assert 65.0 <= airflow <= 75.0

def test_fan_failure_forces_flow_zero(default_airflow_model):
    """
    Tests that simulating fan failure sets obstruction to 1.0 and flow to zero.
    """
    model = default_airflow_model
    model.set_obstruction(0.2) # Initial obstruction
    model.simulate_fan_failure()
    assert abs(model.obstruction_ratio - 1.0) < TOL
    assert abs(model.step() - 0.0) < TOL

def test_reset_sets_obstruction_to_zero(default_airflow_model):
    """
    Tests that resetting the model sets obstruction to 0.0.
    """
    model = default_airflow_model
    model.set_obstruction(0.7) # Set some obstruction
    model.reset()
    assert abs(model.obstruction_ratio - 0.0) < TOL
    airflow = model.step(temperature=20.88)
    assert 95.0 <= airflow <= 105.0
