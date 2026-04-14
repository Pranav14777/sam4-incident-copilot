from pydantic import BaseModel
from typing import Optional, List


class Asset(BaseModel):
    id: int
    name: str
    asset_type: str
    location: str
    site: str
    industry: str
    criticality: str
    install_date: str
    downtime_cost_per_hour: float
    rated_power_kw: Optional[float] = None
    voltage_v: Optional[float] = None
    current_a: Optional[float] = None
    rpm: Optional[int] = None
    efficiency: Optional[float] = None
    transmission_type: Optional[str] = None


class Incident(BaseModel):
    id: int
    asset_id: int
    asset_name: str
    health_status: str
    indicator: str
    failure_mode: str
    severity: str
    location: str
    detected_at: str
    status: str


class MaintenanceRecord(BaseModel):
    id: int
    asset_id: int
    maintenance_type: str
    description: str
    performed_at: str
    performed_by: str


class EnrichedIncident(BaseModel):
    incident: Incident
    asset: Asset
    maintenance_history: List[MaintenanceRecord]
    previous_incidents: List[Incident]
    repeat_incident: bool


class AIRecommendation(BaseModel):
    incident_id: int
    summary: str
    likely_root_cause: str
    urgency: str
    recommended_action: str
    notify: List[str]
    human_review_required: bool
    ticket_title: str
    ticket_body: str
    uncertainty_flagged: bool = False


class WorkOrder(BaseModel):
    id: Optional[int] = None
    incident_id: int
    ticket_title: str
    ticket_body: str
    status: str
    created_at: Optional[str] = None