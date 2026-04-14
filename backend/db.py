import sqlite3
import os

DB_PATH = os.getenv("DB_PATH", "sam4.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            asset_type TEXT NOT NULL,
            location TEXT NOT NULL,
            site TEXT NOT NULL,
            industry TEXT NOT NULL,
            criticality TEXT NOT NULL,
            install_date TEXT NOT NULL,
            downtime_cost_per_hour REAL NOT NULL,
            rated_power_kw REAL,
            voltage_v REAL,
            current_a REAL,
            rpm INTEGER,
            efficiency REAL,
            transmission_type TEXT
        );

        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY,
            asset_id INTEGER NOT NULL,
            asset_name TEXT NOT NULL,
            health_status TEXT NOT NULL,
            indicator TEXT NOT NULL,
            failure_mode TEXT NOT NULL,
            severity TEXT NOT NULL,
            location TEXT NOT NULL,
            detected_at TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'open',
            FOREIGN KEY (asset_id) REFERENCES assets(id)
        );

        CREATE TABLE IF NOT EXISTS maintenance_history (
            id INTEGER PRIMARY KEY,
            asset_id INTEGER NOT NULL,
            maintenance_type TEXT NOT NULL,
            description TEXT NOT NULL,
            performed_at TEXT NOT NULL,
            performed_by TEXT NOT NULL,
            FOREIGN KEY (asset_id) REFERENCES assets(id)
        );

        CREATE TABLE IF NOT EXISTS ai_recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_id INTEGER NOT NULL,
            summary TEXT NOT NULL,
            likely_root_cause TEXT NOT NULL,
            urgency TEXT NOT NULL,
            recommended_action TEXT NOT NULL,
            notify TEXT NOT NULL,
            human_review_required INTEGER NOT NULL,
            ticket_title TEXT NOT NULL,
            ticket_body TEXT NOT NULL,
            uncertainty_flagged INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            FOREIGN KEY (incident_id) REFERENCES incidents(id)
        );

        CREATE TABLE IF NOT EXISTS actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_id INTEGER NOT NULL,
            ticket_title TEXT NOT NULL,
            ticket_body TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'draft',
            created_at TEXT NOT NULL,
            FOREIGN KEY (incident_id) REFERENCES incidents(id)
        );
    """)

    conn.commit()
    conn.close()


def get_all_incidents():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM incidents ORDER BY detected_at DESC").fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_incident_by_id(incident_id: int):
    conn = get_connection()
    row = conn.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_asset_by_id(asset_id: int):
    conn = get_connection()
    row = conn.execute("SELECT * FROM assets WHERE id = ?", (asset_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_maintenance_history(asset_id: int):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM maintenance_history WHERE asset_id = ? ORDER BY performed_at DESC",
        (asset_id,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_previous_incidents(asset_id: int, exclude_id: int):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM incidents WHERE asset_id = ? AND id != ? ORDER BY detected_at DESC LIMIT 5",
        (asset_id, exclude_id)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def save_recommendation(rec: dict):
    conn = get_connection()
    conn.execute("""
        INSERT INTO ai_recommendations
        (incident_id, summary, likely_root_cause, urgency, recommended_action,
         notify, human_review_required, ticket_title, ticket_body, uncertainty_flagged, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        rec["incident_id"], rec["summary"], rec["likely_root_cause"],
        rec["urgency"], rec["recommended_action"], ",".join(rec["notify"]),
        int(rec["human_review_required"]), rec["ticket_title"],
        rec["ticket_body"], int(rec.get("uncertainty_flagged", False)),
        rec["created_at"]
    ))
    conn.commit()
    conn.close()


def save_action(action: dict):
    conn = get_connection()
    conn.execute("""
        INSERT INTO actions (incident_id, ticket_title, ticket_body, status, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (
        action["incident_id"], action["ticket_title"],
        action["ticket_body"], action["status"], action["created_at"]
    ))
    conn.commit()
    conn.close()


def update_incident_status(incident_id: int, status: str):
    conn = get_connection()
    conn.execute("UPDATE incidents SET status = ? WHERE id = ?", (status, incident_id))
    conn.commit()
    conn.close()