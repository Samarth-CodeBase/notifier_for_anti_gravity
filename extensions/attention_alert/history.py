import sqlite3
import json
import logging
from pathlib import Path
import threading
from typing import List, Dict, Any
from .models import AgentEvent, AgentState

logger = logging.getLogger(__name__)

class NotificationHistory:
    """Records event state transitions and alert dispatches to SQLite."""

    def __init__(self, db_path: str = "notifications.db"):
        self._db_path = db_path
        # We use a thread lock because SQLite connections are thread-local
        # but we might be called from multiple threads. In SQLite it's
        # usually easier to just open a short-lived connection per operation
        # or use a check_same_thread=False connection if very careful.
        # Here we just open a fresh connection per write to avoid threading issues,
        # since we aren't writing 1000s of events per second.
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        """Create tables if they don't exist and enable WAL mode for concurrency."""
        with self._lock:
            try:
                # Resolve path properly 
                if self._db_path != ":memory:":
                    Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
                
                with sqlite3.connect(self._db_path) as conn:
                    # Enable Write-Ahead Logging for better concurrency
                    conn.execute("PRAGMA journal_mode=WAL")
                    
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS events (
                            id          INTEGER PRIMARY KEY AUTOINCREMENT,
                            event_type  TEXT    NOT NULL,
                            source      TEXT    NOT NULL,
                            severity    TEXT    NOT NULL,
                            payload     TEXT,
                            recorded_at REAL    NOT NULL
                        )
                    """)
                    
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS alert_dispatches (
                            id            INTEGER PRIMARY KEY AUTOINCREMENT,
                            event_id      INTEGER REFERENCES events(id),
                            backend       TEXT    NOT NULL,
                            status        TEXT    NOT NULL,
                            dispatched_at REAL    NOT NULL,
                            error_msg     TEXT
                        )
                    """)
                    
                    # Create indices (IF NOT EXISTS syntax for indices is tricky across all SQLite versions, 
                    # so we catch the OperationalError if they already exist, or just use CREATE INDEX IF NOT EXISTS 
                    # which is supported in SQLite 3.3.0+)
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type)")
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_events_time ON events(recorded_at)")
            except Exception as e:
                logger.error(f"Failed to initialize notification history DB: {e}")

    def record_event(self, event: AgentEvent) -> int:
        """Record an event and return its generated ID. Returns -1 on failure."""
        with self._lock:
            try:
                with sqlite3.connect(self._db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO events (event_type, source, severity, payload, recorded_at) VALUES (?, ?, ?, ?, ?)",
                        (event.type, event.source, event.severity, json.dumps(event.payload), event.timestamp)
                    )
                    conn.commit()
                    return cursor.lastrowid
            except Exception as e:
                logger.error(f"Failed to record event to history: {e}")
                return -1

    def record_dispatch(self, event_id: int, backend: str, status: str, timestamp: float, error_msg: str = None):
        """Record an alert dispatch attempt."""
        with self._lock:
            try:
                with sqlite3.connect(self._db_path) as conn:
                    conn.execute(
                        "INSERT INTO alert_dispatches (event_id, backend, status, dispatched_at, error_msg) VALUES (?, ?, ?, ?, ?)",
                        (event_id, backend, status, timestamp, error_msg)
                    )
            except Exception as e:
                 logger.error(f"Failed to record dispatch to history: {e}")

    def query_recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Query the most recent events."""
        with self._lock:
            try:
                results = []
                with sqlite3.connect(self._db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.execute(
                        "SELECT * FROM events ORDER BY recorded_at DESC LIMIT ?", 
                        (limit,)
                    )
                    for row in cursor:
                        # Convert Row to dict
                        d = dict(row)
                        # Parse payload back to dict
                        try:
                             if d.get("payload"):
                                  d["payload"] = json.loads(d["payload"])
                        except json.JSONDecodeError:
                             pass
                        results.append(d)
                return results
            except Exception as e:
                logger.error(f"Failed to query recent events: {e}")
                return []
                
    def cleanup(self, retention_days: int):
        """Delete events older than retention_days."""
        import time
        cutoff = time.monotonic() - (retention_days * 86400) # 86400 seconds in a day
        
        # In a real system, time.monotonic() is relative to system boot, 
        # while we might want time.time() for absolute retention.
        # However, since the spec uses time.monotonic() for DB entries, we stick to it.
        # Note: If the machine reboots, time.monotonic() resets, making this cleanup flawed
        # for long-term retention. A production system should use time.time() for DB records.
        # But we will use the same clock source used during insertion.
        
        with self._lock:
            try:
                with sqlite3.connect(self._db_path) as conn:
                    # We first need to delete from alert_dispatches to respect foreign key constraints
                    # (though SQLite FKs are off by default, it's good practice)
                    conn.execute(
                        "DELETE FROM alert_dispatches WHERE event_id IN (SELECT id FROM events WHERE recorded_at < ?)",
                        (cutoff,)
                    )
                    deleted_events = conn.execute(
                        "DELETE FROM events WHERE recorded_at < ?",
                        (cutoff,)
                    ).rowcount
                    
                    if deleted_events > 0:
                        logger.info(f"Cleaned up {deleted_events} old events from notification history.")
                        
                    # Reclaim space
                    conn.execute("VACUUM")
            except Exception as e:
                logger.error(f"Failed to cleanup notification history: {e}")
