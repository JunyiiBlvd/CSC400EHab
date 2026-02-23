import pytest
from backend.simulation.humidity import HumidityModel

def test_deterministic_output_with_seed():
    """Verify that with the same seed, the model is deterministic."""
    model1 = HumidityModel(initial_humidity=50, drift=0.1, noise_amplitude=0.5, random_seed=123)
    model2 = HumidityModel(initial_humidity=50, drift=0.1, noise_amplitude=0.5, random_seed=123)

    history1 = [model1.step() for _ in range(10)]
    history2 = [model2.step() for _ in range(10)]

    assert history1 == history2, "Models with the same seed should produce identical humidity histories."

def test_positive_drift_increases_humidity():
    """Verify that a positive drift increases humidity over time."""
    initial_humidity = 50
    model = HumidityModel(initial_humidity=initial_humidity, drift=0.5, noise_amplitude=0, random_seed=1)
    
    # Run for a few steps
    for _ in range(5):
        model.step()

    assert model.current_humidity > initial_humidity, "Positive drift should increase humidity."

def test_negative_drift_decreases_humidity():
    """Verify that a negative drift decreases humidity over time."""
    initial_humidity = 50
    model = HumidityModel(initial_humidity=initial_humidity, drift=-0.5, noise_amplitude=0, random_seed=1)
    
    # Run for a few steps
    for _ in range(5):
        model.step()

    assert model.current_humidity < initial_humidity, "Negative drift should decrease humidity."

def test_humidity_clamping_at_100():
    """Verify that humidity is clamped at 100."""
    model = HumidityModel(initial_humidity=99, drift=2, noise_amplitude=0.1, random_seed=1)
    
    for _ in range(10):
        model.step()
        assert model.current_humidity <= 100, "Humidity should not exceed 100."
    
    # Check if it eventually reaches and stays at 100 with strong positive drift
    model_strong_drift = HumidityModel(initial_humidity=99, drift=5, noise_amplitude=0, random_seed=1)
    model_strong_drift.step()
    assert model_strong_drift.current_humidity == 100, "Humidity should be clamped at 100."


def test_humidity_clamping_at_0():
    """Verify that humidity is clamped at 0."""
    model = HumidityModel(initial_humidity=1, drift=-2, noise_amplitude=0.1, random_seed=1)
    
    for _ in range(10):
        model.step()
        assert model.current_humidity >= 0, "Humidity should not go below 0."

    # Check if it eventually reaches and stays at 0 with strong negative drift
    model_strong_drift = HumidityModel(initial_humidity=1, drift=-5, noise_amplitude=0, random_seed=1)
    model_strong_drift.step()
    assert model_strong_drift.current_humidity == 0, "Humidity should be clamped at 0."

def test_noise_within_amplitude():
    """Verify that the noise component stays within the specified amplitude."""
    drift = 0.1
    noise_amplitude = 0.5
    
    # We need to check if -noise_amplitude <= noise <= noise_amplitude
    # To isolate noise, we need to know the humidity before and after the step.
    # noise = H(t+1) - H(t) - drift
    # This only holds if clamping does not occur.
    
    for seed in range(20): # Run test with different random seeds
        # Start far from the boundaries to avoid clamping
        model = HumidityModel(initial_humidity=50, drift=drift, noise_amplitude=noise_amplitude, random_seed=seed)
        
        h_t = model.current_humidity
        h_t1 = model.step()

        # This check is only valid if clamping did not happen
        if 0 < h_t1 < 100:
            noise = h_t1 - h_t - drift
            # Using pytest.approx to handle potential floating point inaccuracies
            assert -noise_amplitude <= noise <= noise_amplitude, f"Noise should be within the specified amplitude. Got {noise}"
