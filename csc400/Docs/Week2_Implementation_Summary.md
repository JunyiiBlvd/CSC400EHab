3# Week 2: Implement standalone AirflowModel with unit tests

This document provides a summary of the work completed for the Week 2 implementation of the E-Habitat simulation, focusing on the introduction of a standalone `AirflowModel`. It covers the created/modified files, the testing process, challenges encountered, and instructions to reproduce the verification steps.

## 1. Files Created/Modified

### New Files Created

- **`backend/simulation/airflow.py`**:
  - Contains the `AirflowModel` class, which simulates airflow dynamics within an environment.
  - It initializes with a `nominal_flow` and an optional `obstruction_ratio`.
  - Methods include:
    - `step()`: Updates and returns the `current_flow` based on the `nominal_flow` and `obstruction_ratio`.
    - `set_obstruction(ratio: float)`: Sets the `obstruction_ratio`, ensuring it is clamped between 0.0 and 1.0.
    - `simulate_fan_failure()`: Sets `obstruction_ratio` to 1.0, effectively stopping airflow.
    - `reset()`: Resets `obstruction_ratio` to 0.0 (no obstruction).
- **`backend/tests/test_airflow_model.py`**:
  - Contains unit tests for the `AirflowModel` class, verifying its functionality and adherence to specified constraints.

### Existing Files Modified/Renamed

- **`backend/simulation/thermal_model.py` was renamed to `backend/simulation/thermal.py`**: This was done to modularize the simulation structure, making the `thermal` module more consistent with future `airflow`, `humidity`, and `environment` modules.
- **`backend/simulation/node.py`**: Updated import statement from `from .thermal_model import ThermalModel` to `from .thermal import ThermalModel` to reflect the file rename.
- **`backend/simulation/runner.py`**: Updated import statement from `from .thermal_model import ThermalModel` to `from .thermal import ThermalModel` to reflect the file rename.
- **`backend/tests/test_thermal_model.py` was renamed to `backend/tests/test_thermal.py`**: The test file was renamed to match the new `thermal.py` module name and updated its internal import.
- **`backend/simulation/humidity.py`**: Created as an empty placeholder module with a docstring.
- **`backend/simulation/environment.py`**: Created as an empty placeholder module with a docstring.
- **`.gitignore`**: Updated to include Python cache files (`__pycache__/`, `*.pyc`, `.pytest_cache/`, `venv/`) to prevent them from being tracked by Git.

## 2. Testing Performed

The following tests were successfully executed:

1.  **AirflowModel Unit Tests (`pytest backend/tests/test_airflow_model.py`)**:
    - **`test_no_obstruction_flow_equals_nominal`**: Verified that with 0% obstruction, the `current_flow` matches the `nominal_flow`.
    - **`test_fifty_percent_obstruction_flow_is_half_nominal`**: Confirmed that with 50% obstruction, the `current_flow` is 50% of the `nominal_flow`.
    - **`test_full_obstruction_flow_is_zero`**: Ensured that with 100% obstruction, the `current_flow` is 0.
    - **`test_obstruction_clamped_between_zero_and_one`**: Verified that `set_obstruction` correctly clamps input ratios to be within the [0.0, 1.0] range.
    - **`test_fan_failure_forces_flow_zero`**: Tested that `simulate_fan_failure()` correctly sets `obstruction_ratio` to 1.0, resulting in zero flow.
    - **`test_reset_sets_obstruction_to_zero`**: Confirmed that `reset()` correctly restores the `obstruction_ratio` to 0.0.

2.  **ThermalModel Unit Tests (`pytest backend/tests/test_thermal.py`)**:
    - All previous thermal tests were re-run and passed successfully, confirming no regressions were introduced by the refactoring and new module addition.

## 3. Problems Encountered and Resolutions

During development and testing, an issue with running tests was encountered due to Python's module resolution.

- **Problem**: `ModuleNotFoundError: No module named 'backend'`.
  - When initially attempting to run `pytest backend/tests` or `pytest` from the project root, the test runner failed to locate the `backend` package. This occurred despite the project being installed in editable mode (`pip install -e .`). The system's Python path was not correctly configured to resolve the package imports when invoked in certain ways.

- **Resolution**:
  - The issue was resolved by explicitly invoking `pytest` using `python3 -m pytest`. This command ensures that the Python interpreter's module search path (`sys.path`) is properly configured to include the current directory and allows it to find the installed `backend` package and its submodules (like `backend.simulation.thermal` and `backend.simulation.airflow`).

## 4. How to Repeat Testing

To set up the environment and run the same tests, follow these steps from the project root directory (`/home/junyii/Desktop/Repos/CSC400EHab/csc400`).

**Step 1: Create and Activate a Python Virtual Environment**
This ensures that dependencies are isolated from your system.

```bash
# Create the virtual environment
python3 -m venv venv

# Note: The 'activate' script is used in subsequent steps by referencing
# the venv directly, so manual activation is not strictly required.
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
This command executes the entire test suite (both thermal and airflow tests) using `pytest` installed in the virtual environment.

```bash
venv/bin/python3 -m pytest
```

**Expected Outcome**: All 11 tests (5 thermal, 6 airflow) should pass with no warnings.

## 5. Appendix: Explanation of Generated Files

During the setup and testing process, several files and directories are automatically generated by Python and its packaging tools. Here is an explanation of what they are and why they are needed.

### `__init__.py`

- **Purpose**: This empty file acts as a signal to the Python interpreter that the directory containing it should be treated as a "package" (a collection of modules).
- **Why it was used**: We created `__init__.py` in the `backend/` and `backend/simulation/` directories. This allows us to write clear, absolute imports like `from backend.simulation.thermal_model import ThermalModel`, which is a robust way to structure code in larger projects. Without this file, Python would not know how to find the modules in those directories.

### `__pycache__` and `.pyc` files

- **Purpose**: When you run a Python script, the interpreter first compiles it into a lower-level representation called "bytecode". This bytecode is then executed. To save time on future runs, Python stores this bytecode in a `__pycache__` directory.
- **Details**: The files inside, ending in `.cpython-312.pyc`, are the cached bytecode. The name indicates the Python implementation (`cpython`) and version (`3.12`) used. If you run the script again and the source `.py` file hasn't changed, Python will skip the compilation step and run the bytecode directly, making the program start faster.
- **Note**: These are temporary cache files and should not be committed to version control. They are generated automatically as needed.

### `csc400.egg-info` directory

- **Purpose**: This directory is automatically created by `setuptools` (a standard Python packaging library) when a package is installed. It contains essential metadata about the project.
- **Why it was created**: When we ran `pip install -e .`, `setuptools` created this directory to store information about our `csc400` package, such as its name, version, and a list of all files it includes.
- **Note**: This directory is an artifact of the installation process that allows Python to manage the package correctly. The name "egg" refers to an older Python packaging format, but the `.egg-info` directory remains a standard for editable installs. It is crucial for making the project importable during development but is not typically edited manually.
