# Edge Anomaly Detection Architecture

This document describes the implementation of real-time anomaly detection within the `VirtualNode`, following an **Edge Computing Architecture** pattern.

## 1. Edge Detection Concept
In this architecture, anomaly detection is performed directly at the "edge"—within the simulated compute node itself—rather than at a centralized cloud or backend service. 
- **Decentralized Intelligence:** Each node is responsible for monitoring its own health.
- **Immediate Response:** Detection happens locally at the source of data generation.

## 2. Data Flow
The internal telemetry and inference pipeline within a `VirtualNode` follows these steps:

1. **Environment Step:** `EnvironmentalModel` calculates new raw sensor values (Thermal, Airflow, Humidity).
2. **CPU Load:** `VirtualNode` generates the current CPU utilization.
3. **Telemetry Packaging:** Raw values are bundled into a telemetry dictionary.
4. **Feature Extraction:** The telemetry is passed to the `SlidingWindowFeatureExtractor`.
5. **Inference:** If the window is full, the `AnomalyModel` (Isolation Forest) processes the features.
6. **Enriched Telemetry:** The original telemetry is updated with `anomaly_score` and `is_anomaly` flags.
7. **Broadcast:** The final enriched packet is returned by the `step()` method.

## 3. Sliding Window Lifecycle
The detection system relies on temporal context provided by the sliding window:
- **Warm-up Phase:** For the first 9 steps of a node's lifecycle, the window is "filling." No inference is performed.
- **Active Phase:** From step 10 onwards, every new data point triggers a new inference call based on the most recent 10 seconds of data.
- **Continuous Update:** The window automatically discards the oldest data point as a new one arrives (FIFO).

## 4. Telemetry Schema Changes
The telemetry packet emitted by `VirtualNode` has been expanded to include detection results:

| Field | Type | Description |
|---|---|---|
| `temperature` | float | Current node temperature in Celsius. |
| ... | ... | (Other standard sensor fields) |
| `anomaly_score` | float \| None | The raw output from the Isolation Forest decision function. |
| `is_anomaly` | boolean | True if the current window indicates abnormal behavior. |

*Note: `anomaly_score` is `None` during the warm-up phase.*

## 5. Why Inference Occurs Locally
- **Bandwidth Efficiency:** We don't need to stream high-frequency raw data to a central server for analysis. Only the final "verdict" needs to be reported.
- **Privacy/Security:** Sensitive raw telemetry stays within the node's local context.
- **Resilience:** The node can continue to detect anomalies even if connection to a central dashboard is intermittent.

## 6. Latency Implications
- **Computational Overhead:** Running the `IsolationForest.predict()` method adds a negligible amount of time (milliseconds) to each simulation step.
- **Detection Delay:** Due to the window size of 10, a sudden anomaly may take 1-2 steps to significantly impact the statistical features (like variance or ROC) enough to trigger a flag.

## 7. Limitations
- **Cold Start:** Anomaly detection is effectively blind for the first 10 seconds of operation.
- **Local Context Only:** The edge model cannot see what is happening in neighboring nodes. It cannot detect cluster-wide anomalies (e.g., a data center cooling failure) that haven't affected its local sensors yet.
- **Static Model:** The model stored on the "edge" must be manually updated/retrained if the definition of "normal" behavior changes.

## 8. Alignment with SRS
This implementation fulfills the SRS requirement for **Real-time Edge Analysis**, ensuring that the simulation engine is not just a data generator, but an intelligent monitor of its own state.
