# Week 1: Thermal Model Implementation Summary

This document provides a summary of the work completed for the Week 1 implementation of the E-Habitat thermal physics engine. It covers the created files, the testing process, challenges encountered, and instructions to reproduce the verification steps.

## 1. Files Created

The following file structure was created in the `backend/` directory:

```
backend/
├── __init__.py
├── simulation/
│   ├── __init__.py
│   ├── thermal_model.py
│   ├── node.py
│   └── runner.py
└── tests/
    └── test_thermal_model.py
```

### File Descriptions

-   **`backend/simulation/thermal_model.py`**: Contains the `ThermalModel` class, which implements the core physics equations for temperature change based on CPU load and environmental factors.
-   **`backend/simulation/node.py`**: Defines the `VirtualNode` class, a wrapper that uses a `ThermalModel` instance and simulates a node by generating CPU load and producing telemetry data.
-   **`backend/simulation/runner.py`**: A command-line interface (CLI) script to execute the simulation. It can run for a specified duration, accept a random seed for deterministic output, and save results to a CSV file.
-   **`backend/tests/test_thermal_model.py`**: Contains unit tests for the `ThermalModel` and `VirtualNode` classes to ensure correctness, including temperature dynamics, input clamping, and deterministic behavior.
-   **`backend/__init__.py`**, **`backend/simulation/__init__.py`**: Empty files created to ensure the directories are treated as Python packages, which is necessary for the import system to function correctly.

A `pyproject.toml` was also created at the root to define the project structure for installation, and a `venv` directory was created for a virtual environment.

## 2. Testing Performed

The following tests were successfully executed:

1.  **Unit Tests (`pytest`)**:
    -   **`test_temperature_increases_with_cpu_load`**: Verified that temperature rises when CPU load is high (100%).
    -   **`test_temperature_decreases_when_hot`**: Verified that temperature falls when CPU load is zero and the node's temperature is above the ambient temperature.
    -   **`test_cpu_load_clamping`**: Ensured that `cpu_load` values outside the `[0, 1]` range are correctly clamped.
    -   **`test_deterministic_output_with_seed`**: Confirmed that running the simulation with the same random seed produces identical results, and different seeds produce different results.
    -   **`test_no_temperature_change_at_equilibrium`**: Checked that the temperature remains stable when heat generation and cooling are balanced.

2.  **Simulation Run**:
    -   The `runner.py` script was executed for a 10-second duration (`python -m backend.simulation.runner --duration 10`).
    -   This successfully produced 10 telemetry records printed to the console, confirming that the simulation loop and output functionality work as expected.

## 3. Problems Encountered and Resolutions

During development and testing, we faced a significant challenge related to Python's import system.

-   **Problem**: `ImportError: attempted relative import with no known parent package` and `ModuleNotFoundError: No module named 'backend'`.
    -   The initial test runs failed because `pytest` could not locate the simulation modules (`thermal_model.py`, `node.py`) when the tests were trying to import them. The test files were in a different subdirectory (`tests/`) from the simulation code (`simulation/`), and Python's default path did not include the project's root directory.

-   **Resolution Steps**:
    1.  **Attempt 1 (Absolute Imports)**: The relative imports (`from ..simulation...`) were changed to absolute imports (`from backend.simulation...`). An `__init__.py` file was added to the `backend/` directory to mark it as a Python package. This alone was not sufficient.
    2.  **Attempt 2 (Editable Install)**: To make the `backend` package available across the entire project for the Python interpreter, a `pyproject.toml` file was created to define the project structure. The project was then installed in "editable" mode using the command `pip install -e .`. This command creates a link to the source code in the virtual environment's `site-packages`, making the `backend` package importable from anywhere within the project. This successfully resolved the import errors and allowed the tests to pass.

-   **Problem**: `DeprecationWarning: datetime.datetime.utcnow() is deprecated`.
    -   The tests produced warnings because the `datetime.utcnow()` function is deprecated in recent Python versions.

-   **Resolution**:
    -   The code in `backend/simulation/node.py` was updated to use the recommended, timezone-aware alternative: `datetime.now(timezone.utc)`. The necessary `from datetime import timezone` was also added. This eliminated the warnings.

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

**Step 3: Run the Unit Tests**
This command executes the test suite using the `pytest` installed in the virtual environment.

```bash
venv/bin/pytest backend/tests/
```
**Expected Outcome**: All 5 tests should pass with no warnings.

**Step 4: Run the Simulation**
This executes the CLI runner for a short duration to verify its functionality.

```bash
venv/bin/python -m backend.simulation.runner --duration 10
```
**Expected Outcome**: The script will print 10 lines of telemetry data to the console, one per second. Each line will be a dictionary containing `node_id`, `timestamp`, `temperature`, and `cpu_load`.

## 5. Appendix: Explanation of Generated Files

During the setup and testing process, several files and directories are automatically generated by Python and its packaging tools. Here is an explanation of what they are and why they are needed.

### `__init__.py`
-   **Purpose**: This empty file acts as a signal to the Python interpreter that the directory containing it should be treated as a "package" (a collection of modules).
-   **Why it was used**: We created `__init__.py` in the `backend/` and `backend/simulation/` directories. This allows us to write clear, absolute imports like `from backend.simulation.thermal_model import ThermalModel`, which is a robust way to structure code in larger projects. Without this file, Python would not know how to find the modules in those directories.

### `__pycache__` and `.pyc` files
-   **Purpose**: When you run a Python script, the interpreter first compiles it into a lower-level representation called "bytecode". This bytecode is then executed. To save time on future runs, Python stores this bytecode in a `__pycache__` directory.
-   **Details**: The files inside, ending in `.cpython-312.pyc`, are the cached bytecode. The name indicates the Python implementation (`cpython`) and version (`3.12`) used. If you run the script again and the source `.py` file hasn't changed, Python will skip the compilation step and run the bytecode directly, making the program start faster.
-   **Note**: These are temporary cache files and should not be committed to version control. They are generated automatically as needed.

### `csc400.egg-info` directory
-   **Purpose**: This directory is automatically created by `setuptools` (a standard Python packaging library) when a package is installed. It contains essential metadata about the project.
-   **Why it was created**: When we ran `pip install -e .`, `setuptools` created this directory to store information about our `csc400` package, such as its name, version, and a list of all files it includes.
-   **Note**: This directory is an artifact of the installation process that allows Python to manage the package correctly. The name "egg" refers to an older Python packaging format, but the `.egg-info` directory remains a standard for editable installs. It is crucial for making the project importable during development but is not typically edited manually.
