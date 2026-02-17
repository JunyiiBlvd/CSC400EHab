# Week 2.2: Integrate EnvironmentalModel and Update VirtualNode Telemetry

This document summarizes the work completed for the E-Habitat simulation, focusing on the integration of `ThermalModel`, `AirflowModel`, and `HumidityModel` into a new `EnvironmentalModel`, and the subsequent update of `VirtualNode` and the simulation `runner`. It covers the created/modified files, the testing process, and instructions to reproduce the verification steps, including a demonstration of the engine's full capabilities.

## 1. Files Created/Modified

### New Files Created

-   **`backend/simulation/environment.py`**:
    -   Contains the `EnvironmentalModel` class, which composes `ThermalModel`, `AirflowModel`, and `HumidityModel`.
    -   Its `step()` method orchestrates the stepping of all three sub-models and returns a dictionary containing the latest `temperature`, `airflow`, and `humidity` values.
-   **`backend/tests/test_environment_model.py`**:
    -   Contains unit tests for the `EnvironmentalModel` class, verifying its functionality. Tests include:
        -   `test_step_returns_correct_dictionary`: Ensures the `step()` method returns a dictionary with the expected keys and values from its composed models.
        -   `test_deterministic_behavior_with_seed`: Verifies that the `EnvironmentalModel` produces deterministic outputs when instantiated with models using the same random seed.

### Existing Files Modified

-   **`backend/simulation/node.py`**:
    -   Modified to replace direct `ThermalModel` usage with the new `EnvironmentalModel`.
    -   The `VirtualNode`'s `step()` method now calls `environmental_model.step(cpu_load)` and extracts `temperature`, `humidity`, and `airflow` from the returned dictionary.
    -   The telemetry output has been updated to include `humidity` and `airflow` in addition to `node_id`, `timestamp`, `temperature`, and `cpu_load`.
    -   Deterministic seed behavior for CPU load generation was preserved.
-   **`backend/simulation/runner.py`**:
    -   Updated to instantiate `ThermalModel`, `AirflowModel`, and `HumidityModel`.
    -   These individual models are then wrapped into an `EnvironmentalModel` instance.
    -   The `EnvironmentalModel` is then passed to the `VirtualNode` constructor.
-   **`backend/tests/test_thermal.py`**:
    -   The `test_deterministic_output_with_seed` was updated to correctly instantiate `VirtualNode` with an `EnvironmentalModel` instead of a `ThermalModel`, fixing a `TypeError` that arose from the changes in `node.py`.

## 2. Testing Performed

The following tests were successfully executed:

1.  **EnvironmentalModel Unit Tests (`pytest backend/tests/test_environment_model.py`)**:
    -   `test_step_returns_correct_dictionary`: Confirmed that `EnvironmentalModel.step()` provides the expected telemetry format.
    -   `test_deterministic_behavior_with_seed`: Verified that the composed model maintains deterministic behavior when a seed is provided.
2.  **All Existing Unit Tests (`pytest backend/tests`)**:
    -   All previous thermal, airflow, and humidity tests were re-run and passed successfully. This included fixing the `test_deterministic_output_with_seed` in `test_thermal.py` which was impacted by the `VirtualNode` change. No regressions were introduced.
3.  **CLI Runner Output Verification**:
    -   The `backend/simulation/runner.py` script was executed, and its output was inspected to confirm that the telemetry data now includes `temperature`, `humidity`, and `airflow` as required.

## 3. Problems Encountered and Resolutions

-   **Problem**: A `TypeError: 'float' object is not subscriptable` occurred in `backend/simulation/node.py` during `pytest`. This was traced to `backend/tests/test_thermal.py` where the `test_deterministic_output_with_seed` test was still passing a `ThermalModel` directly to `VirtualNode`, which now expected an `EnvironmentalModel`. When `VirtualNode` called `environmental_model.step()`, it was calling `ThermalModel.step()` which returns a float, leading to the error when `VirtualNode` tried to access dictionary keys on it.
-   **Resolution**: The `test_deterministic_output_with_seed` in `backend/tests/test_thermal.py` was updated to correctly instantiate a `ThermalModel`, `AirflowModel`, and `HumidityModel`, wrap them in an `EnvironmentalModel`, and then pass this `EnvironmentalModel` to the `VirtualNode`, resolving the type mismatch.

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
This command executes the entire test suite (thermal, airflow, humidity, and environment tests) using `pytest` installed in the virtual environment.

```bash
venv/bin/python3 -m pytest
```
**Expected Outcome**: All 19 tests (5 thermal, 6 airflow, 6 humidity, 2 environment) should pass with no warnings.

## 5. Demonstration of Engine's Full Capabilities (Telemetry Output)

To see the combined telemetry output from the `EnvironmentalModel` via the `VirtualNode` and `runner`, execute the following command:

```bash
venv/bin/python3 -m backend.simulation.runner --duration 5 --seed 1
```

This will run the simulation for 5 steps with a fixed seed (for reproducibility) and print the telemetry for each step to the console. You should observe output similar to:

```json
{'node_id': 'node-1', 'timestamp': '...', 'temperature': ..., 'humidity': ..., 'airflow': ..., 'cpu_load': ...}
```
where `temperature`, `humidity`, and `airflow` values dynamically change based on their respective models.
