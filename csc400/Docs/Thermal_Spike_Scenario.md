# Thermal Spike Anomaly Scenario

This document describes the implementation and usage of the manual thermal spike anomaly injection within the E-Habitat simulation.

## 1. Purpose of Controlled Anomaly Injection
Controlled injection allows for the empirical validation of the anomaly detection system. By introducing known deviations, we can:
- Measure the **sensitivity** of the Isolation Forest.
- Calculate **detection latency** (time from injection to `is_anomaly=True`).
- Verify that the telemetry stream correctly labels ground-truth anomalies via the `injected_anomaly` flag.

## 2. Immediate vs. Gradual Anomaly
- **Immediate (Implementation):** A thermal spike is a "step change." The temperature increases by a fixed magnitude instantly. This is typical of sensor failure or sudden hardware malfunctions.
- **Gradual:** A slow "drift" over time. This is more typical of accumulating dust on fans or gradual HVAC degradation. The current implementation focuses on the immediate spike for high-contrast testing.

## 3. Implementation Design
The `VirtualNode` maintains an internal state for anomaly injection:
- `spike_remaining_steps`: A counter that decrements each time `step()` is called.
- `spike_magnitude`: The amount of Celsius to add to the raw environmental temperature.

When `spike_remaining_steps > 0`, the temperature is artificially inflated, and the `injected_anomaly` flag is set to `True` in the telemetry.

## 4. Interaction with Isolation Forest
Because the Isolation Forest is trained on "normal" data (without spikes), a sudden increase in temperature—especially one that breaks the learned statistical patterns (mean, variance, ROC)—will result in a significantly lower anomaly score.
- **Detection:** If the spike is large enough, `is_anomaly` will switch from `False` to `True`.
- **Temporal Effect:** Since we use a 10-step sliding window, a 1-step spike will affect the window's features for the next 10 seconds.

## 5. Demo Usage Instructions
To trigger a thermal spike programmatically:

```python
# Create node as usual
node = VirtualNode(...)

# Inject a 10-degree spike that lasts for 5 seconds
node.inject_thermal_spike(duration_seconds=5, magnitude=10.0)

# In the next 5 steps, telemetry will show:
# "temperature": [baseline + 10.0]
# "injected_anomaly": True
```

## 6. Known Limitations
- **Additivity:** Spikes are added to the environmental temperature. If multiple spikes are called in quick succession, the last call overwrites the previous state rather than stacking.
- **Single Variable:** Currently only supports temperature spikes.

## 7. Planned Future Scenarios
As the simulation evolves, we plan to implement:
- **HVAC Failure:** A gradual, exponential increase in ambient temperature.
- **Airflow Blockage:** A sudden drop in the `airflow` value to simulate a physical obstruction or fan motor failure.
- **Sensor Noise:** Injecting high-frequency random noise into any telemetry variable to test the model's robustness against "dirty" data.

## 8. SRS Alignment
This feature directly supports **SRS Section 6 (Diagnostic & Fault Tolerance Testing)**, providing the tools necessary for system stress testing and validation.
