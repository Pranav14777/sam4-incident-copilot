import httpx
import os
import sqlite3
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
DB_PATH = os.getenv("DB_PATH", "sam4.db")


def _log_notification(incident_id: int, channel: str, status: str, message: str):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS notification_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_id INTEGER NOT NULL,
            channel TEXT NOT NULL,
            status TEXT NOT NULL,
            message TEXT NOT NULL,
            sent_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        INSERT INTO notification_log (incident_id, channel, status, message, sent_at)
        VALUES (?, ?, ?, ?, ?)
    """, (incident_id, channel, status, message, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()


def format_slack_message(recommendation: dict, incident: dict, asset: dict) -> dict:
    urgency = recommendation.get("urgency", "unknown").upper()

    urgency_emoji = {
        "CRITICAL": "🔴",
        "HIGH": "🟠",
        "MEDIUM": "🟡",
        "LOW": "🟢"
    }.get(urgency, "⚪")

    notify_list = ", ".join(recommendation.get("notify", []))
    human_review = "✅ Yes — Human approval required" if recommendation.get("human_review_required") else "❌ No"
    uncertainty = "⚠️ Yes" if recommendation.get("uncertainty_flagged") else "No"

    message = {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{urgency_emoji} SAM4 Incident Triage — {urgency}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Asset:*\n{incident['asset_name']}"},
                    {"type": "mrkdwn", "text": f"*Location:*\n{incident['location']}"},
                    {"type": "mrkdwn", "text": f"*Failure Mode:*\n{incident['failure_mode']}"},
                    {"type": "mrkdwn", "text": f"*Indicator:*\n{incident['indicator']}"}
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Summary:*\n{recommendation['summary']}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Recommended Action:*\n{recommendation['recommended_action']}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Notify:*\n{notify_list}"},
                    {"type": "mrkdwn", "text": f"*Human Review Required:*\n{human_review}"},
                    {"type": "mrkdwn", "text": f"*Uncertainty Flagged:*\n{uncertainty}"},
                    {"type": "mrkdwn", "text": f"*Ticket:*\n{recommendation['ticket_title']}"}
                ]
            },
            {
                "type": "divider"
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"🏭 SAM4 Incident Copilot | Asset criticality: {asset['criticality'].upper()} | Downtime cost: €{asset['downtime_cost_per_hour']}/hr"
                    }
                ]
            }
        ]
    }
    return message


def send_slack_notification(recommendation: dict, incident: dict, asset: dict) -> dict:
    message = format_slack_message(recommendation, incident, asset)
    plain_text = f"[SAM4] {recommendation['ticket_title']} — {incident['asset_name']} at {incident['location']}"

    # If no real webhook URL configured, log as mock
    if not SLACK_WEBHOOK_URL or "mock" in SLACK_WEBHOOK_URL:
        _log_notification(
            incident_id=incident["id"],
            channel="slack-mock",
            status="mock_sent",
            message=plain_text
        )
        return {
            "status": "mock_sent",
            "channel": "slack-mock",
            "message": plain_text,
            "note": "Mock webhook — replace SLACK_WEBHOOK_URL in .env with real Slack webhook to enable"
        }

    # Real webhook call
    try:
        response = httpx.post(
            SLACK_WEBHOOK_URL,
            json=message,
            timeout=10.0
        )
        response.raise_for_status()
        _log_notification(
            incident_id=incident["id"],
            channel="slack",
            status="sent",
            message=plain_text
        )
        return {"status": "sent", "channel": "slack", "message": plain_text}

    except Exception as e:
        _log_notification(
            incident_id=incident["id"],
            channel="slack",
            status="failed",
            message=f"Error: {str(e)}"
        )
        return {"status": "failed", "channel": "slack", "error": str(e)}