"""
Centralized anomaly detection server.

Receives raw telemetry from VirtualNodes, runs the same Isolation Forest
inference pipeline independently, and records detection timestamps for
latency comparison against edge detection.
"""
import json
import time
from typing import Any, Dict, Optional

from ..ml.feature_extraction import SlidingWindowFeatureExtractor
from ..ml.model_loader import ModelLoader


class CentralServer:
    """
    Mirrors VirtualNode ML inference, but centralized.

    Each node gets its own SlidingWindowFeatureExtractor and anomaly persistence
    window (20 steps), identical to VirtualNode. Detection timestamps are recorded
    on the False→True persistent-anomaly transition so latency_delta_ms reflects
    the real gap between edge and central detection.
    """

    ANOMALY_PERSISTENCE_STEPS = 20

    def __init__(self, model_loader: ModelLoader):
        """
        Args:
            model_loader: Shared ModelLoader instance (same one used by VirtualNodes).
        """
        self.model = model_loader

        # Per-node sliding windows and persistence state
        self._extractors: Dict[str, SlidingWindowFeatureExtractor] = {}
        self._anomaly_flags: Dict[str, list] = {}   # rolling window of raw bool flags
        self._prev_persistent: Dict[str, bool] = {} # last persistent state per node

        # Per-node stats / event records
        self._records: Dict[str, Dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_node(self, node_id: str) -> None:
        """Lazily initialise per-node state on first telemetry received."""
        if node_id not in self._extractors:
            self._extractors[node_id] = SlidingWindowFeatureExtractor(window_size=10)
            self._anomaly_flags[node_id] = []
            self._prev_persistent[node_id] = False
            self._records[node_id] = {
                "injection_ts": None,
                "edge_detection_ts": None,
                "central_detection_ts": None,
                "edge_latency_ms": None,
                "central_latency_ms": None,
                "latency_delta_ms": None,
                "bytes_edge": None,
                "bytes_central": 0,
                "last_updated": None,
            }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def receive_telemetry(
        self,
        node_id: str,
        raw_telemetry: dict,
        seq_id: int,
        edge_detection_ts: Optional[float],
        bytes_edge: Optional[int] = None,
    ) -> None:
        """
        Feed one telemetry step from a node into the central pipeline.

        Args:
            node_id: Source node identifier (e.g. "node-1").
            raw_telemetry: Dict with keys temperature, humidity, airflow, cpu_load.
                           Must NOT contain anomaly_score / is_anomaly — raw only.
            seq_id: Step sequence number from the originating node.
            edge_detection_ts: time.time() value from when the edge node first
                               transitioned to persistent anomaly, or None if the
                               edge has not yet detected an anomaly.
            bytes_edge: Byte size of the full edge telemetry frame (including
                        anomaly fields). Pass this from the API layer when available.
        """
        self._ensure_node(node_id)
        record = self._records[node_id]

        # Track bandwidth: accumulate bytes received by central
        record["bytes_central"] += len(json.dumps(raw_telemetry).encode())
        record["last_updated"] = time.time()

        if bytes_edge is not None:
            if record["bytes_edge"] is None:
                record["bytes_edge"] = 0
            record["bytes_edge"] += bytes_edge

        # Store latest edge detection timestamp when provided
        if edge_detection_ts is not None:
            record["edge_detection_ts"] = edge_detection_ts

        # Feed into this node's sliding window
        extractor = self._extractors[node_id]
        extractor.add_point(raw_telemetry)

        if not extractor.is_window_ready():
            return

        # Run inference
        features = extractor.extract_features()
        result = self.model.predict(features)
        raw_flag: bool = result["is_anomaly"]

        # Mirror VirtualNode anomaly persistence (20-step rolling window)
        flags = self._anomaly_flags[node_id]
        flags.append(raw_flag)
        self._anomaly_flags[node_id] = flags[-self.ANOMALY_PERSISTENCE_STEPS:]
        persistent_anomaly = any(flags)

        # Record central_detection_ts on False → True transition only
        prev = self._prev_persistent[node_id]
        if persistent_anomaly and not prev:
            record["central_detection_ts"] = time.time()
            injection_ts = record["injection_ts"]
            if record["edge_detection_ts"] is not None:
                delta_ms = (record["central_detection_ts"] - record["edge_detection_ts"]) * 1000
                record["latency_delta_ms"] = round(delta_ms, 3)
            if injection_ts is not None:
                if record["edge_detection_ts"] is not None:
                    record["edge_latency_ms"] = round(
                        (record["edge_detection_ts"] - injection_ts) * 1000, 3
                    )
                record["central_latency_ms"] = round(
                    (record["central_detection_ts"] - injection_ts) * 1000, 3
                )

        self._prev_persistent[node_id] = persistent_anomaly

    '''
    def record_injection(self, node_id: str, injection_ts: float) -> None:
        """Called when an anomaly is injected. Stores injection timestamp
        so edge_latency_ms and central_latency_ms can be computed."""
        self._ensure_node(node_id)
        self._records[node_id]["injection_ts"] = injection_ts
    '''

    def record_injection(self, node_id: str, injection_ts: float) -> None:
        self._ensure_node(node_id)

        self._records[node_id].update({
            "injection_ts": injection_ts,
            "edge_detection_ts": None,
            "central_detection_ts": None,
            "edge_latency_ms": None,
            "central_latency_ms": None,
            "latency_delta_ms": None,
            "bytes_edge": None,
            "bytes_central": 0,
            "last_updated": None,
        })

        self._anomaly_flags[node_id] = []
        self._prev_persistent[node_id] = False
        
    def get_status(self) -> Dict[str, Any]:
        """
        Return per-node detection and bandwidth statistics.

        Returns a dict keyed by node_id. Each value contains:
            edge_detection_ts    — epoch seconds when edge first detected anomaly
            central_detection_ts — epoch seconds when central first detected anomaly
            edge_latency_ms      — ms from injection to edge detection (None until wired)
            central_latency_ms   — ms from injection to central detection (None until wired)
            latency_delta_ms     — central_detection_ts − edge_detection_ts in ms
            bytes_edge           — byte size of edge frames (including anomaly payload)
            bytes_central        — cumulative bytes received by central (raw telemetry only)
            last_updated         — epoch seconds of last received telemetry
        """
        return {
            node_id: {
                "edge_detection_ts": r["edge_detection_ts"],
                "central_detection_ts": r["central_detection_ts"],
                "edge_latency_ms": r["edge_latency_ms"],
                "central_latency_ms": r["central_latency_ms"],
                "latency_delta_ms": r["latency_delta_ms"],
                "bytes_edge": r["bytes_edge"],
                "bytes_central": r["bytes_central"],
                "last_updated": r["last_updated"],
            }
            for node_id, r in self._records.items()
        }
