import sqlite3
from pathlib import Path

# DB file path relative to project root
DB_DIR = Path("db")
DB_PATH = DB_DIR / "ehabitat.db"


def _ensure_column(
    cursor: sqlite3.Cursor,
    table_name: str,
    column_name: str,
    column_def: str,
):
    cursor.execute(f"PRAGMA table_info({table_name})")
    existing = {row[1] for row in cursor.fetchall()}
    if column_name not in existing:
        cursor.execute(
            f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def}"
        )


def init_db():
    """Initializes the database, creates tables and indices if they don't exist."""
    if not DB_DIR.exists():
        DB_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS profiles (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT NOT NULL UNIQUE,
            created_at REAL NOT NULL
        )
        """
    )

    cursor.execute(
        """
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
            anomaly_score REAL,
            profile_id    INTEGER
        )
        """
    )

    cursor.execute(
        """
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
            bytes_central        INTEGER,
            profile_id           INTEGER
        )
        """
    )

    _ensure_column(cursor, "telemetry", "profile_id", "INTEGER")
    _ensure_column(cursor, "anomaly_events", "profile_id", "INTEGER")

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_profiles_name ON profiles(name)")
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_telemetry_timestamp ON telemetry(timestamp)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_telemetry_node_id ON telemetry(node_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_telemetry_profile_id ON telemetry(profile_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_anomaly_events_profile_id ON anomaly_events(profile_id)"
    )

    conn.commit()
    conn.close()


def get_profiles() -> list:
    query = "SELECT id, name, created_at FROM profiles ORDER BY LOWER(name) ASC"
    try:
        conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"Database error in get_profiles: {e}")
        return []


def create_profile(name: str) -> dict:
    cleaned = name.strip()
    if not cleaned:
        raise ValueError("Profile name is required")

    try:
        conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO profiles (name, created_at) VALUES (?, strftime('%s', 'now'))",
            (cleaned,),
        )
        conn.commit()
        profile_id = cursor.lastrowid
        cursor.execute(
            "SELECT id, name, created_at FROM profiles WHERE id = ?",
            (profile_id,),
        )
        row = cursor.fetchone()
        conn.close()
        return dict(row)
    except sqlite3.IntegrityError:
        raise ValueError("A profile with that name already exists")


def insert_telemetry(record: dict):
    """Inserts one row into telemetry. Dict keys must match column names."""
    query = """
        INSERT INTO telemetry (
            seq_id, node_id, timestamp, temperature, humidity,
            airflow, cpu_load, is_anomaly, anomaly_score, profile_id
        ) VALUES (
            :seq_id, :node_id, :timestamp, :temperature, :humidity,
            :airflow, :cpu_load, :is_anomaly, :anomaly_score, :profile_id
        )
    """
    try:
        conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        conn.execute(query, record)
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Database error in insert_telemetry: {e}")


def insert_anomaly_event(record: dict):
    """Inserts one row into anomaly_events. Dict keys must match column names."""
    query = """
        INSERT INTO anomaly_events (
            seq_id, node_id, injection_timestamp, edge_detection_ts,
            central_detection_ts, edge_latency_ms, central_latency_ms,
            detection_source, bytes_edge, bytes_central, profile_id
        ) VALUES (
            :seq_id, :node_id, :injection_timestamp, :edge_detection_ts,
            :central_detection_ts, :edge_latency_ms, :central_latency_ms,
            :detection_source, :bytes_edge, :bytes_central, :profile_id
        )
    """
    try:
        conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        conn.execute(query, record)
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Database error in insert_anomaly_event: {e}")


def get_anomaly_events(profile_id: int | None = None) -> list:
    """Returns anomaly rows ordered by injection_timestamp DESC."""
    query = "SELECT * FROM anomaly_events"
    params: list[int] = []

    if profile_id is not None:
        query += " WHERE profile_id = ?"
        params.append(profile_id)

    query += " ORDER BY injection_timestamp DESC"

    try:
        conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"Database error in get_anomaly_events: {e}")
        return []


def get_telemetry_range(
    node_id: str,
    start: float,
    end: float,
    profile_id: int | None = None,
) -> list:
    """Returns telemetry rows for node_id between start and end timestamps, ordered ASC."""
    query = """
        SELECT * FROM telemetry
        WHERE node_id = ? AND timestamp >= ? AND timestamp <= ?
    """
    params: list[float | str | int] = [node_id, start, end]

    if profile_id is not None:
        query += " AND profile_id = ?"
        params.append(profile_id)

    query += " ORDER BY timestamp ASC"

    try:
        conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"Database error in get_telemetry_range: {e}")
        return []
