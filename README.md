# SAM4 Incident Copilot

An AI-powered incident triage and workflow automation system for industrial health monitoring, inspired by the SAM4 platform by Samotics.

## Overview

When industrial equipment fails, maintenance teams receive raw incident alerts — but lack the context, prioritisation, and recommended actions needed to respond quickly. This system automates that triage process end-to-end.

Given a health incident (e.g. a pump showing stator fault due to current unbalance), the pipeline:

1. Receives the structured incident payload
2. Enriches it with asset history, criticality, and past maintenance records
3. Calls an LLM to generate a structured recommendation (root cause, urgency, next action)
4. Validates the output against business rules (escalation logic, uncertainty flagging)
5. Creates a draft work order stored in the database
6. Sends a mock notification to the maintenance team via webhook (Slack)
7. Exposes everything through a clean dashboard UI

## Why This Exists

This project demonstrates how GenAI and automation can reduce manual triage work, improve response consistency, and connect incident detection to downstream maintenance workflows — the kind of internal operational leverage that industrial companies need at scale.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, FastAPI |
| Database | SQLite |
| LLM Integration | Groq API (LLaMA 3) |
| Notifications | Webhook (mock Slack) |
| Frontend | HTML, CSS, JavaScript |
| Containerisation | Docker, Docker Compose |

## Project Structure

```
sam4-incident-copilot/
│
├── backend/
│   ├── main.py          # FastAPI app and route definitions
│   ├── db.py            # Database setup and queries
│   ├── llm.py           # LLM prompt construction and API call
│   ├── models.py        # Pydantic data models
│   └── seed_data.py     # Mock assets and incidents for demo
│
├── frontend/
│   └── index.html       # Dashboard UI
│
├── docker-compose.yml   # Multi-container setup
├── Dockerfile           # Backend container definition
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variable template
└── README.md
```

## Getting Started

### Prerequisites

- Docker and Docker Compose installed
- A Groq API key (free at [groq.com](https://groq.com))

### Setup

**1. Clone the repository**

```bash
git clone https://github.com/Pranav14777/sam4-incident-copilot.git
cd sam4-incident-copilot
```

**2. Create your environment file**

```bash
cp .env.example .env
```

**3. Add your Groq API key to `.env`**

```
GROQ_API_KEY=your_key_here
```

**4. Build and run with Docker Compose**

```bash
docker-compose up --build
```

**5. Open the dashboard at `http://localhost:8000`**

## Pipeline Architecture

```
Incident Payload
       │
       ▼
Asset Context Enrichment
(SQLite: asset history, criticality, maintenance records)
       │
       ▼
LLM Triage
(Groq / LLaMA 3: root cause, urgency, recommended action)
       │
       ▼
Validation Rules Engine
(escalation logic, uncertainty flagging, approval gates)
       │
       ├──────────────────────┐
       ▼                      ▼
Work Order Created       Slack Webhook
(stored in SQLite)       (mock notification)
       │
       ▼
Dashboard UI
```

## Example Output

Given an incident with:
- **Asset:** Pump-204
- **Indicator:** Current unbalance > 10%
- **Failure mode:** Stator fault

The system generates:

```json
{
  "summary": "Pump-204 has shown sustained current unbalance exceeding 10% since detection. Risk of insulation degradation is high.",
  "likely_root_cause": "High resistance in cable connections from MCC to motor, or early-stage stator winding fault.",
  "urgency": "critical",
  "recommended_action": "Inspect cable connections from MCC. Megger the motor to verify insulation integrity. Check grounding.",
  "notify": ["maintenance-team", "reliability-engineer"],
  "human_review_required": true,
  "ticket_title": "CRITICAL: Stator fault detected on Pump-204 - immediate inspection required",
  "ticket_body": "SAM4 has detected a current unbalance on Pump-204 exceeding threshold for an extended period. Immediate cable and insulation inspection recommended."
}
```

## Validation Rules

- Critical severity incidents always require human approval before action
- Repeated incidents within 14 days are automatically escalated
- If asset history is missing, output is flagged with uncertainty
- Shutdown is never recommended unless severity and confidence both meet threshold

## Roadmap

- [ ] Persistent feedback loop to improve recommendations over time
- [ ] PostgreSQL for production-grade data persistence
- [ ] Authentication and role-based access
- [ ] Real Slack and Jira integrations
- [ ] Multi-site and multi-asset support