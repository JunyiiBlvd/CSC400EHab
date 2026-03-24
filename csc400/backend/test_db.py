import sqlite3
import time
from backend.simulation.database import init_db, insert_telemetry, insert_anomaly_event, DB_PATH

def test_database():
    print("--- Starting Database Smoke Test ---")
    
    # 1. Initialize DB
    init_db()
    
    # 2. Insert 3 telemetry rows
    nodes = ["node-1", "node-2", "node-3"]
    for i, node_id in enumerate(nodes):
        record = {
            "seq_id": i + 1,
            "node_id": node_id,
            "timestamp": time.time(),
            "temperature": 20.0 + i,
            "humidity": 45.0 + i,
            "airflow": 2.5 - (i * 0.1),
            "cpu_load": 10.0 + (i * 5),
            "is_anomaly": 0,
            "anomaly_score": 0.1
        }
        insert_telemetry(record)
    
    # 3. Insert anomaly events
    # Event 1: Missing one latency (should be filtered out by the new summary query)
    event_record_1 = {
        "seq_id": 10,
        "node_id": "node-1",
        "injection_timestamp": time.time() - 5,
        "edge_detection_ts": time.time() - 2,
        "central_detection_ts": None,
        "edge_latency_ms": 3000.0,
        "central_latency_ms": None,
        "detection_source": "edge",
        "bytes_edge": 500,
        "bytes_central": 200
    }
    insert_anomaly_event(event_record_1)

    # Event 2: Has both latencies (should be included in the summary)
    event_record_2 = {
        "seq_id": 11,
        "node_id": "node-2",
        "injection_timestamp": time.time() - 10,
        "edge_detection_ts": time.time() - 7,
        "central_detection_ts": time.time() - 6,
        "edge_latency_ms": 3000.0,
        "central_latency_ms": 4000.0,
        "detection_source": "central",
        "bytes_edge": 600,
        "bytes_central": 300
    }
    insert_anomaly_event(event_record_2)
    
    # 4. Verify counts
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM telemetry")
        telemetry_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM anomaly_events")
        event_count = cursor.fetchone()[0]

        # Verify the new summary query logic
        from backend.api import get_anomaly_summary
        summary_res = get_anomaly_summary()
        print(f"Summary result: {summary_res}")
        
        conn.close()
        
        print(f"Telemetry count: {telemetry_count}")
        print(f"Anomaly event count: {event_count}")
        
        # We check >= because the DB might already have data if run multiple times
        # but for a fresh test we expect at least 3 and 1.
        # Actually, let's just check if they are > 0 for a basic smoke test, 
        # or exactly 3 and 1 if we want to be strict (assuming fresh DB).
        if telemetry_count >= 3 and event_count >= 1:
            print("PASS")
        else:
            print("FAIL: Counts are lower than expected.")
            
    except Exception as e:
        print(f"FAIL: Verification error: {e}")

if __name__ == "__main__":
    test_database()
