import sqlite3
import os
from pathlib import Path

# DB file path relative to project root
DB_DIR = Path("db")
DB_PATH = DB_DIR / "ehabitat.db"

def init_db():
    """Initializes the database, creates tables and indices if they don't exist."""
    if not DB_DIR.exists():
        DB_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    cursor = conn.cursor()

    # Create telemetry table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS telemetry (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            seq_id        INTEGER NOT NULL,
            node_id       TEXT NOT NULL,
            timestamp     REAL NOT NULL,
            temperature   REAL,
            humidity      REAL,
            airflow       REAL,
            cpu_load      REAL,
            is_anomaly    INTEGER,
            anomaly_score REAL
        )
    """)

    # Create anomaly_events table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS anomaly_events (
            id                   INTEGER PRIMARY KEY AUTOINCREMENT,
            seq_id               INTEGER NOT NULL,
            node_id              TEXT NOT NULL,
            injection_timestamp  REAL,
            edge_detection_ts    REAL,
            central_detection_ts REAL,
            edge_latency_ms      REAL,
            central_latency_ms   REAL,
            detection_source     TEXT,
            bytes_edge           INTEGER,
            bytes_central        INTEGER
        )
    """)

    # Create indices for performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_timestamp ON telemetry(timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_node_id ON telemetry(node_id)")

    conn.commit()
    conn.close()

def insert_telemetry(record: dict):
    """Inserts one row into telemetry. Dict keys must match column names."""
    query = """
        INSERT INTO telemetry (
            seq_id, node_id, timestamp, temperature, humidity, 
            airflow, cpu_load, is_anomaly, anomaly_score
        ) VALUES (
            :seq_id, :node_id, :timestamp, :temperature, :humidity, 
            :airflow, :cpu_load, :is_anomaly, :anomaly_score
        )
    """
    try:
        conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        conn.execute(query, record)
        conn.commit()
        conn.close()
    except Exception as e:
        # A failed database write must NEVER crash the application
        print(f"Database error in insert_telemetry: {e}")

def insert_anomaly_event(record: dict):
    """Inserts one row into anomaly_events. Dict keys must match column names."""
    query = """
        INSERT INTO anomaly_events (
            seq_id, node_id, injection_timestamp, edge_detection_ts,
            central_detection_ts, edge_latency_ms, central_latency_ms,
            detection_source, bytes_edge, bytes_central
        ) VALUES (
            :seq_id, :node_id, :injection_timestamp, :edge_detection_ts,
            :central_detection_ts, :edge_latency_ms, :central_latency_ms,
            :detection_source, :bytes_edge, :bytes_central
        )
    """
    try:
        conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        conn.execute(query, record)
        conn.commit()
        conn.close()
    except Exception as e:
        # A failed database write must NEVER crash the application
        print(f"Database error in insert_anomaly_event: {e}")

def get_anomaly_events() -> list:
    """Returns all rows from anomaly_events ordered by injection_timestamp DESC."""
    query = "SELECT * FROM anomaly_events ORDER BY injection_timestamp DESC"
    try:
        conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"Database error in get_anomaly_events: {e}")
        return []

def get_telemetry_range(node_id: str, start: float, end: float) -> list:
    """Returns telemetry rows for node_id between start and end timestamps, ordered ASC."""
    query = """
        SELECT * FROM telemetry
        WHERE node_id = ? AND timestamp >= ? AND timestamp <= ?
        ORDER BY timestamp ASC
    """
    try:
        conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query, (node_id, start, end))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"Database error in get_telemetry_range: {e}")
        return []
