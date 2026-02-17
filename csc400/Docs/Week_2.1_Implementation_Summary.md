# Week 2.1: Implement standalone HumidityModel with deterministic noise

This document summarizes the work completed for the E-Habitat simulation, focusing on the introduction of a standalone `HumidityModel`. It covers the created/modified files, the testing process, and instructions to reproduce the verification steps.

## 1. Files Created/Modified

### New Files Created

-   **`backend/simulation/humidity.py`**:
    -   Contains the `HumidityModel` class, which simulates humidity changes within an environment.
    -   It initializes with `initial_humidity`, `drift`, `noise_amplitude`, and an optional `random_seed`.
    -   Methods include:
        -   `step()`: Updates and returns the `current_humidity` based on the `drift` and a random `noise` component.
        -   Humidity is clamped between 0 and 100.
-   **`backend/tests/test_humidity_model.py`**:
    -   Contains unit tests for the `HumidityModel` class, verifying its functionality and adherence to specified constraints.

### Existing Files Modified/Renamed

-   None.

## 2. Testing Performed

The following tests were successfully executed:

1.  **HumidityModel Unit Tests (`pytest backend/tests/test_humidity_model.py`)**:
    -   **`test_deterministic_output_with_seed`**: Verified that with the same seed, the model produces identical humidity histories, ensuring deterministic noise.
    -   **`test_positive_drift_increases_humidity`**: Confirmed that a positive drift value causes the humidity to increase over time (when noise is zero).
    -   **`test_negative_drift_decreases_humidity`**: Ensured that a negative drift value causes the humidity to decrease over time (when noise is zero).
    -   **`test_humidity_clamping_at_100`**: Verified that the humidity level does not exceed 100, even with strong positive drift.
    -   **`test_humidity_clamping_at_0`**: Verified that the humidity level does not go below 0, even with strong negative drift.
    -   **`test_noise_within_amplitude`**: Confirmed that the random noise added during each step remains within the specified `noise_amplitude`.

2.  **Existing Unit Tests**:
    -   All previous thermal and airflow tests were re-run and passed successfully, confirming no regressions were introduced by the new module addition.

## 3. Problems Encountered and Resolutions

-   No significant problems were encountered during the implementation or testing of the `HumidityModel`.

## 4. How to Repeat Testing

To set up the environment and run the same tests, follow these steps from the project root directory (`/home/junyii/Desktop/Repos/CSC400EHab/csc400`).

**Step 1: Create and Activate a Python Virtual Environment**
This ensures that dependencies are isolated from your system.

```bash
# Create the virtual environment
python3 -m venv venv
```

**Step 2: Install Dependencies**
This includes `pytest` for running tests and installs the project itself in editable mode.

```bash
# Install pytest
venv/bin/pip install pytest

# Install the project in editable mode to make the 'backend' package available
venv/bin/pip install -e .
```

**Step 3: Run All Unit Tests**
This command executes the entire test suite (thermal, airflow, and humidity tests) using `pytest` installed in the virtual environment.

```bash
venv/bin/python3 -m pytest
```
**Expected Outcome**: All 17 tests (5 thermal, 6 airflow, 6 humidity) should pass with no warnings.
