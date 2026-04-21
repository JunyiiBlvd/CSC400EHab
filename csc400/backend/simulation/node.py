"""
This module defines the VirtualNode, which wraps thermal, airflow, and humidity models 
to simulate a single compute node.
"""
import random
from datetime import datetime, timezone
from typing import Optional

from .thermal_model import ThermalModel
from .airflow import AirflowModel
from .humidity import HumidityModel
from ..ml.feature_extraction import SlidingWindowFeatureExtractor
from ..ml.model_loader import ModelLoader


class VirtualNode:
    """
    Represents a simulated node with its own thermal model, airflow model, 
    humidity model, and CPU load generation.
    """

    def __init__(
        self,
        node_id: str,
        thermal_model: ThermalModel,
        airflow_model: AirflowModel,
        humidity_model: HumidityModel,
        random_seed: Optional[int] = None,
    ):
        """
        Initializes the VirtualNode.

        Args:
            node_id (str): A unique identifier for the node.
            thermal_model (ThermalModel): The thermal model instance.
            airflow_model (AirflowModel): The airflow model instance.
            humidity_model (HumidityModel): The humidity model instance.
            random_seed (Optional[int]): An optional seed for the random number
                                         generator to ensure deterministic runs.
        """
        self.node_id = node_id
        self.thermal_model = thermal_model
        self.airflow_model = airflow_model
        self.humidity_model = humidity_model
        if random_seed is not None:
            self.rng = random.Random(random_seed)
        else:
            self.rng = random.Random()
        
        # Anomaly Injection State
        self.spike_remaining_steps = 0
        self.cpu_load_override = 0.0
        self.hvac_lag_steps = 0
        self._frozen_airflow = None
        self.hvac_failure_remaining_steps = 0
        self.hvac_failure_total_steps = 0
        self.coolant_leak_active = False
        self.coolant_leak_remaining_steps = 0
        self.coolant_leak_base_humidity = 0.0
        
        # Anomaly Persistence State
        self.recent_anomaly_flags = []
        self.anomaly_persistence_steps = 20
        
        # AR(1) CPU Load State
        self.cpu_load_state = 0.5

        # ML Inference State
        self.feature_extractor = SlidingWindowFeatureExtractor(window_size=10)
        try:
            self.anomaly_model = ModelLoader()
        except FileNotFoundError:
            self.anomaly_model = None
            print(f'[{self.node_id}] Warning: No model found, anomaly detection disabled')
        except Exception as e:
            self.anomaly_model = None
            print(f'[{self.node_id}] Warning: Failed to load model ({e}), anomaly detection disabled')

    def reset_anomaly_state(self):
        """Resets the ML feature window and anomaly persistence flags."""
        self.recent_anomaly_flags = []
        self.feature_extractor = SlidingWindowFeatureExtractor(window_size=10)

    def inject_thermal_spike(self, duration_seconds: int = 120, lag_seconds: int = 40):
        """
        Manually injects a thermal spike anomaly by overriding CPU load.

        Args:
            duration_seconds (int): How many steps the spike should last.
            lag_seconds (int): How many steps the HVAC should lag (unresponsive).
        """
        self.cpu_load_override = 1.0
        self.spike_remaining_steps = duration_seconds
        self.hvac_lag_steps = lag_seconds
        # Reduce airflow to 15% during lag - HVAC not responding
        self._frozen_airflow = self.airflow_model.current_flow * 0.15

    def inject_hvac_failure(self, duration_seconds: int = 40):
        """
        Injects an HVAC failure by linearly ramping airflow down to zero over the
        first 15 steps, then holding at full blockage for the remainder of the duration.

        Unlike simulate_fan_failure(), this keeps air_roc non-zero for ~25 steps,
        sustaining the anomaly signal across the full sliding window fill cycle.

        After duration_seconds steps the failure clears and normal airflow resumes.

        Args:
            duration_seconds (int): Total steps the failure lasts.
        """
        self.hvac_failure_remaining_steps = duration_seconds
        self.hvac_failure_total_steps = duration_seconds

    def inject_coolant_leak(self):
        """
        Injects a coolant leak by overriding humidity with a steep ramp.

        Humidity rises by 2.5% RH per step from the current value, capped at 85.0.
        The ramp runs for 20 steps then holds at the capped value until cleared.
        """
        self.coolant_leak_active = True
        self.coolant_leak_remaining_steps = 20
        self.coolant_leak_base_humidity = self.humidity_model.current_humidity

    def _generate_cpu_load(self) -> float:
        """
        Generates a CPU load using an AR(1) process or returns an override if a spike is active.

        Returns:
            float: The CPU load (0.1 to 0.9).
        """
        if self.spike_remaining_steps > 0:
            self.spike_remaining_steps -= 1
            return self.cpu_load_override
            
        # AR(1) Process: target 0.5, autocorrelation 0.95
        noise = self.rng.gauss(0, 0.02)
        self.cpu_load_state = (0.95 * self.cpu_load_state + 0.05 * 0.5 + noise)
        
        # Clamp between 0.1 and 0.9
        self.cpu_load_state = max(0.1, min(0.9, self.cpu_load_state))
        return self.cpu_load_state

    def step(self) -> dict:
        """
        Advances the node's simulation by one step and returns its telemetry.

        Correct physical feedback loop:
        1. Generate CPU load
        2. HVAC responds to PREVIOUS step temperature (self.thermal_model.temperature)
        3. New airflow affects current step cooling
        4. Temperature changes based on new cooling
        5. Humidity responds to the NEW temperature
        """
        # 1. Generate CPU load
        cpu_load = self._generate_cpu_load()
        
        # 2. Airflow responds to last step's temperature
        '''
        if self.hvac_failure_remaining_steps > 0:
            elapsed = self.hvac_failure_total_steps - self.hvac_failure_remaining_steps
            ramp_ratio = min(1.0, elapsed / 15.0)
            current_airflow = self.airflow_model.nominal_flow * (1.0 - ramp_ratio)
            self.airflow_model.current_flow = current_airflow
            self.hvac_failure_remaining_steps -= 1
        elif self.hvac_lag_steps > 0:
        '''
        if self.hvac_failure_remaining_steps > 0:
            elapsed = self.hvac_failure_total_steps - self.hvac_failure_remaining_steps
            ramp_ratio = min(1.0, elapsed / 15.0)

            self.airflow_model.obstruction_ratio = ramp_ratio
            current_airflow = self.airflow_model.nominal_flow * (1.0 - ramp_ratio)
            self.airflow_model.current_flow = current_airflow

            self.hvac_failure_remaining_steps -= 1

            if self.hvac_failure_remaining_steps == 0:
                    self.airflow_model.obstruction_ratio = 0.0
        elif self.hvac_lag_steps > 0:
            current_airflow = self._frozen_airflow
            self.hvac_lag_steps -= 1
        else:
            current_airflow = self.airflow_model.step(temperature=self.thermal_model.temperature)
        
        # 3. Calculate airflow ratio for cooling efficiency
        airflow_ratio = (
            current_airflow / self.airflow_model.nominal_flow 
            if self.airflow_model.nominal_flow > 0 else 0.0
        )
        
        # 4. Thermal update (converts CPU load to heat and uses airflow for cooling)
        temperature = self.thermal_model.step(cpu_load, airflow_ratio=airflow_ratio)
            
        # 5. Humidity update (now COUPLED to the NEW temperature)
        current_humidity = self.humidity_model.step(temperature)

        # Coolant leak override — applied after physics, before ML
        if self.coolant_leak_active:
            if self.coolant_leak_remaining_steps > 0:
                current_humidity = min(
                    85.0,
                    self.coolant_leak_base_humidity + 2.5 * (20 - self.coolant_leak_remaining_steps)
                )
                self.coolant_leak_remaining_steps -= 1
            else:
                # current_humidity = min(85.0, self.coolant_leak_base_humidity + 50.0)
                self.coolant_leak_active = False
                self.humidity_model.current_humidity = current_humidity
                
        telemetry = {
            "node_id": self.node_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "temperature": temperature,
            "humidity": current_humidity,
            "airflow": current_airflow,
            "cpu_load": cpu_load
        }

        # 6. ML Inference
        self.feature_extractor.add_point(telemetry)
        if self.anomaly_model and self.feature_extractor.is_window_ready():
            features = self.feature_extractor.extract_features()
            ml_result = self.anomaly_model.predict(features)
            
            raw_anomaly = ml_result['is_anomaly']
            self.recent_anomaly_flags.append(raw_anomaly)
            self.recent_anomaly_flags = (
                self.recent_anomaly_flags[-self.anomaly_persistence_steps:]
            )
            persistent_anomaly = any(self.recent_anomaly_flags)
            
            telemetry['anomaly_score'] = ml_result['anomaly_score']
            telemetry['is_anomaly'] = persistent_anomaly
        else:
            telemetry['anomaly_score'] = None
            telemetry['is_anomaly'] = False

        return telemetry
