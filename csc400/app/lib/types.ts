export type Telemetry = {
  node_id: string;
  timestamp: string;

  temperature: number;
  cpu_load: number;

  airflow?: number;
  humidity?: number;
  obstruction_ratio?: number;

  anomaly_score?: number | null;
  is_anomaly?: boolean | null;
};

export type AlertItem = {
  id: string;
  ts: string;
  level: "info" | "warn" | "crit";
  message: string;
};