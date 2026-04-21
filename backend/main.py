from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

from db import (init_db, get_all_incidents, get_incident_by_id,
                get_asset_by_id, get_maintenance_history,
                get_previous_incidents, save_recommendation,
                save_action, update_incident_status)
from seed_data import seed
from llm import call_llm, validate_recommendation
from notifications import send_slack_notification

app = FastAPI(title="SAM4 Incident Copilot", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="../frontend"), name="static")


@app.get("/")
def serve_frontend():
    return FileResponse("../frontend/index.html")


@app.on_event("startup")
def startup():
    init_db()
    seed()


@app.get("/health")
def health_check():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


@app.get("/incidents")
def list_incidents():
    incidents = get_all_incidents()
    return {"incidents": incidents, "total": len(incidents)}


@app.get("/incidents/{incident_id}")
def get_incident(incident_id: int):
    incident = get_incident_by_id(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@app.get("/incidents/{incident_id}/enrich")
def enrich_incident(incident_id: int):
    incident = get_incident_by_id(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    asset = get_asset_by_id(incident["asset_id"])
    maintenance = get_maintenance_history(incident["asset_id"])
    previous = get_previous_incidents(incident["asset_id"], incident_id)

    repeat_incident = False
    for prev in previous:
        prev_date = datetime.fromisoformat(prev["detected_at"])
        curr_date = datetime.fromisoformat(incident["detected_at"])
        if abs((curr_date - prev_date).days) <= 14:
            repeat_incident = True
            break

    return {
        "incident": incident,
        "asset": asset,
        "maintenance_history": maintenance,
        "previous_incidents": previous,
        "repeat_incident": repeat_incident
    }


@app.post("/incidents/{incident_id}/triage")
def triage_incident(incident_id: int):
    # Step 1: Get enriched context
    incident = get_incident_by_id(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    asset = get_asset_by_id(incident["asset_id"])
    maintenance = get_maintenance_history(incident["asset_id"])
    previous = get_previous_incidents(incident["asset_id"], incident_id)

    repeat_incident = False
    for prev in previous:
        prev_date = datetime.fromisoformat(prev["detected_at"])
        curr_date = datetime.fromisoformat(incident["detected_at"])
        if abs((curr_date - prev_date).days) <= 14:
            repeat_incident = True
            break

    enriched = {
        "incident": incident,
        "asset": asset,
        "maintenance_history": maintenance,
        "previous_incidents": previous,
        "repeat_incident": repeat_incident
    }

    # Step 2: Call LLM
    recommendation = call_llm(enriched)

    # Step 3: Validate against business rules
    recommendation = validate_recommendation(recommendation, enriched)

    # Step 4: Save recommendation to database
    recommendation["incident_id"] = incident_id
    recommendation["created_at"] = datetime.utcnow().isoformat()
    save_recommendation(recommendation)

    # Step 5: Create draft work order
    action = {
        "incident_id": incident_id,
        "ticket_title": recommendation["ticket_title"],
        "ticket_body": recommendation["ticket_body"],
        "status": "draft",
        "created_at": datetime.utcnow().isoformat()
    }
    save_action(action)

    # Step 6: Update incident status
    update_incident_status(incident_id, "triaged")

    # Step 7: Send Slack notification
    notification = send_slack_notification(recommendation, incident, asset)

    return {
        "recommendation": recommendation,
        "work_order": action,
        "notification": notification,
        "enriched_context": enriched
    }


@app.get("/notifications")
def list_notifications():
    import sqlite3
    db_path = os.getenv("DB_PATH", "sam4.db")
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM notification_log ORDER BY sent_at DESC"
        ).fetchall()
        conn.close()
        return {"notifications": [dict(r) for r in rows]}
    except Exception:
        return {"notifications": []}