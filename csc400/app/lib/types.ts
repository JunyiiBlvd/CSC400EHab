export type Telemetry = {
  node_id: string;
  timestamp: string;

  temperature: number;
  cpu_load: number;

  airflow: number;
  humidity: number;
  obstruction_ratio: number;

  anomaly_score: number | null;
  is_anomaly: boolean | null;
};

export type MlStatus = {
  model_loaded: boolean;
  model_path: string;
  model_load_error: string | null;
  window_size: number;
  window_ready: boolean;
  points_in_window: number;
};

export type AlertItem = {
  id: string;
  ts: string;
  level: "info" | "warn" | "crit";
  message: string;
};