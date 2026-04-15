import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def build_prompt(enriched: dict) -> str:
    incident = enriched["incident"]
    asset = enriched["asset"]
    maintenance = enriched["maintenance_history"]
    previous = enriched["previous_incidents"]
    repeat = enriched["repeat_incident"]

    maintenance_text = "\n".join([
        f"- [{r['performed_at']}] {r['maintenance_type']}: {r['description']} (by {r['performed_by']})"
        for r in maintenance
    ]) or "No maintenance history available."

    previous_text = "\n".join([
        f"- [{p['detected_at']}] {p['health_status']}: {p['indicator']} / {p['failure_mode']} (status: {p['status']})"
        for p in previous
    ]) or "No previous incidents on record."

    prompt = f"""
You are an industrial reliability engineer AI assistant working with the SAM4 condition monitoring platform by Samotics.

Your job is to analyse a health incident detected via Electrical Signature Analysis (ESA) and produce a structured triage recommendation for the maintenance team.

---

INCIDENT DETAILS:
- Asset: {incident['asset_name']}
- Health Status: {incident['health_status']}
- Indicator: {incident['indicator']}
- Failure Mode: {incident['failure_mode']}
- Severity: {incident['severity']}
- Location: {incident['location']}
- Detected At: {incident['detected_at']}
- Repeat Incident (within 14 days): {repeat}

ASSET PASSPORT:
- Type: {asset['asset_type']}
- Site: {asset['site']}
- Industry: {asset['industry']}
- Criticality: {asset['criticality']}
- Installed: {asset['install_date']}
- Rated Power: {asset.get('rated_power_kw', 'N/A')} kW
- Voltage: {asset.get('voltage_v', 'N/A')} V
- Current: {asset.get('current_a', 'N/A')} A
- RPM: {asset.get('rpm', 'N/A')}
- Efficiency: {asset.get('efficiency', 'N/A')}
- Transmission: {asset.get('transmission_type', 'N/A')}
- Downtime Cost: €{asset['downtime_cost_per_hour']}/hour

MAINTENANCE HISTORY:
{maintenance_text}

PREVIOUS INCIDENTS ON THIS ASSET:
{previous_text}

---

Based on all of the above, produce a triage recommendation as a JSON object with exactly these fields:

{{
  "summary": "2-3 sentence summary of the situation and risk",
  "likely_root_cause": "Most probable root cause based on the indicator and failure mode",
  "urgency": "critical | high | medium | low",
  "recommended_action": "Specific step-by-step maintenance action to take",
  "notify": ["list", "of", "roles", "to", "notify"],
  "human_review_required": true or false,
  "ticket_title": "Short title for the work order ticket",
  "ticket_body": "Full work order description for the maintenance team",
  "uncertainty_flagged": true or false
}}

Rules:
- If severity is critical, always set human_review_required to true
- If repeat_incident is true, escalate urgency and mention it explicitly
- If maintenance history is missing, set uncertainty_flagged to true
- Never recommend shutdown unless urgency is critical AND human_review_required is true
- Use precise technical language appropriate for industrial maintenance teams
- Return ONLY the JSON object, no preamble, no explanation, no markdown formatting
"""
    return prompt.strip()


def call_llm(enriched: dict) -> dict:
    prompt = build_prompt(enriched)

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are an industrial reliability engineer AI. You always respond with valid JSON only."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2,
        max_tokens=1000
    )

    raw = response.choices[0].message.content.strip()

    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    return json.loads(raw)


def validate_recommendation(rec: dict, enriched: dict) -> dict:
    incident = enriched["incident"]
    repeat = enriched["repeat_incident"]

    # Rule 1: Critical incidents always require human review
    if incident["severity"] == "critical":
        rec["human_review_required"] = True

    # Rule 2: Repeat incidents get escalated
    if repeat and rec["urgency"] not in ["critical", "high"]:
        rec["urgency"] = "high"
        rec["summary"] = f"[REPEAT INCIDENT - AUTO ESCALATED] " + rec["summary"]

    # Rule 3: Missing maintenance history flags uncertainty
    if not enriched["maintenance_history"]:
        rec["uncertainty_flagged"] = True

    # Rule 4: Never recommend shutdown unless critical + human review
    if "shutdown" in rec["recommended_action"].lower():
        if not (incident["severity"] == "critical" and rec["human_review_required"]):
            rec["recommended_action"] = rec["recommended_action"].replace(
                "shutdown", "inspection"
            )

    return rec