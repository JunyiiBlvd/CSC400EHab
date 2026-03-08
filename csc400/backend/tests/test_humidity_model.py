import pytest
import numpy as np
from backend.simulation.humidity import HumidityModel

def test_deterministic_output_with_seed():
    """Verify that with the same seed, the model is deterministic."""
    model1 = HumidityModel(initial_humidity=50, drift=0.1, noise_amplitude=0.5, random_seed=123)
    model2 = HumidityModel(initial_humidity=50, drift=0.1, noise_amplitude=0.5, random_seed=123)

    history1 = [model1.step() for _ in range(10)]
    history2 = [model2.step() for _ in range(10)]

    assert history1 == history2, "Models with the same seed should produce identical humidity histories."

def test_positive_drift_increases_humidity():
    """Verify that a positive drift increases humidity over time.
    Note: Mean reversion pulls it back, so we check direction.
    """
    initial_humidity = 50
    # Strong drift to overcome initial reversion
    model = HumidityModel(initial_humidity=initial_humidity, drift=2.0, noise_amplitude=0, random_seed=1)
    
    # Run for a few steps
    model.step()

    assert model.current_humidity > initial_humidity, "Positive drift should increase humidity."

def test_negative_drift_decreases_humidity():
    """Verify that a negative drift decreases humidity over time."""
    initial_humidity = 50
    # Strong drift to overcome initial reversion
    model = HumidityModel(initial_humidity=initial_humidity, drift=-2.0, noise_amplitude=0, random_seed=1)
    
    # Run for a few steps
    model.step()

    assert model.current_humidity < initial_humidity, "Negative drift should decrease humidity."

def test_humidity_clamping_at_100():
    """Verify that humidity is clamped near 100 with strong drift.
    Note: Mean reversion pulls away from boundary.
    """
    # Strong drift and high initial to force clamping/high RH
    model = HumidityModel(initial_humidity=45, drift=10, noise_amplitude=0, random_seed=1)
    
    for _ in range(20):
        model.step()
    
    # With drift=10 and reversion = -0.05*(H-45)
    # Steady state: 10 - 0.05*(H-45) = 0 => 200 = H-45 => H=245 (clamped to 100)
    assert model.current_humidity == 100.0

def test_humidity_clamping_at_0():
    """Verify that humidity is clamped near 0 with strong negative drift."""
    # Strong negative drift and low initial to force clamping/low RH
    model = HumidityModel(initial_humidity=45, drift=-10, noise_amplitude=0, random_seed=1)
    
    for _ in range(20):
        model.step()
        
    assert model.current_humidity == 0.0

def test_noise_within_amplitude():
    """Verify that the noise component stays within the specified amplitude."""
    drift = 0.0
    noise_amplitude = 0.5
    
    # To isolate noise, we use drift=0 and reference_temp=21 and temp=21
    # Also initial_humidity=50 and current_humidity=50 to make reversion=0
    
    for seed in range(20):
        model = HumidityModel(initial_humidity=50, drift=drift, noise_amplitude=noise_amplitude, random_seed=seed, reference_temp=21.0)
        
        h_t = model.current_humidity # 50.0
        h_t1 = model.step(temperature=21.0) # reversion=0, coupling=0, drift=0

        noise = h_t1 - h_t
        assert -noise_amplitude <= noise <= noise_amplitude
