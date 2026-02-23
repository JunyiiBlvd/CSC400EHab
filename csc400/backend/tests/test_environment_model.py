import pytest
from unittest.mock import MagicMock
from backend.simulation.environment import EnvironmentalModel
from backend.simulation.thermal import ThermalModel
from backend.simulation.airflow import AirflowModel
from backend.simulation.humidity import HumidityModel

def test_step_returns_correct_dictionary():
    """Verify that the step method returns a dictionary with the correct keys."""
    # Create mock models
    mock_thermal = MagicMock(spec=ThermalModel)
    mock_airflow = MagicMock(spec=AirflowModel)
    mock_humidity = MagicMock(spec=HumidityModel)

    # Configure mock return values
    mock_thermal.step.return_value = 25.5
    mock_airflow.step.return_value = 1.2
    mock_humidity.step.return_value = 45.0

    # Instantiate the EnvironmentalModel with mocks
    env_model = EnvironmentalModel(
        thermal_model=mock_thermal,
        airflow_model=mock_airflow,
        humidity_model=mock_humidity,
    )

    # Call the step method
    cpu_load = 0.5
    result = env_model.step(cpu_load)

    # Assert that the underlying models' step methods were called
    mock_thermal.step.assert_called_once_with(cpu_load)
    mock_airflow.step.assert_called_once()
    mock_humidity.step.assert_called_once()

    # Assert that the returned dictionary has the correct keys and values
    expected_keys = ["temperature", "airflow", "humidity"]
    assert all(key in result for key in expected_keys), "Result dictionary is missing keys."
    assert result["temperature"] == 25.5
    assert result["airflow"] == 1.2
    assert result["humidity"] == 45.0

def test_deterministic_behavior_with_seed():
    """Verify that two models with the same seed produce identical output."""
    # Common parameters for deterministic models
    seed = 42
    initial_temp = 20.0
    initial_humidity = 50.0
    nominal_flow = 1.5

    # Create the first set of models
    thermal1 = ThermalModel(initial_temperature=initial_temp, ambient_temperature=15, air_mass=1, heat_capacity=1000, heat_coefficient=100, cooling_coefficient=5)
    airflow1 = AirflowModel(nominal_flow=nominal_flow)
    humidity1 = HumidityModel(initial_humidity=initial_humidity, drift=0.1, noise_amplitude=0.5, random_seed=seed)
    env_model1 = EnvironmentalModel(thermal_model=thermal1, airflow_model=airflow1, humidity_model=humidity1)

    # Create the second set of models
    thermal2 = ThermalModel(initial_temperature=initial_temp, ambient_temperature=15, air_mass=1, heat_capacity=1000, heat_coefficient=100, cooling_coefficient=5)
    airflow2 = AirflowModel(nominal_flow=nominal_flow)
    humidity2 = HumidityModel(initial_humidity=initial_humidity, drift=0.1, noise_amplitude=0.5, random_seed=seed)
    env_model2 = EnvironmentalModel(thermal_model=thermal2, airflow_model=airflow2, humidity_model=humidity2)

    # Run both models for several steps
    history1 = [env_model1.step(cpu_load=0.6) for _ in range(10)]
    history2 = [env_model2.step(cpu_load=0.6) for _ in range(10)]

    # Assert that the histories are identical
    assert history1 == history2, "Models with the same seed should produce identical environmental histories."
