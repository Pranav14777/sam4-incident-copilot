from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os

from db import init_db, get_all_incidents, get_incident_by_id, get_asset_by_id, get_maintenance_history, get_previous_incidents
from seed_data import seed

app = FastAPI(title="SAM4 Incident Copilot", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


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