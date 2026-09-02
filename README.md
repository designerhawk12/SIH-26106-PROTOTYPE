# AI-Powered Email Threat Detection, GeoLocation and Forensic Intelligence Platform

Contract-first scaffold for an SIH cybersecurity platform that analyzes hostile email evidence, enriches observed indicators, explains deterministic risk, and supports forensic investigation.

No feature logic or frontend has been implemented in this scaffold.

## Architecture

The system is split into six analysis layers and a thin API/persistence boundary:

```text
Untrusted RFC 5322 upload
        |
        v
Email forensics -> AI detection -> Threat intelligence
        |                 |                |
        +-----------------+----------------+
                          |
               Infrastructure geolocation
                          |
                  Deterministic risk engine
                          |
             Timeline, evidence, forensic report
```

- `backend/app/schemas/` is the authoritative shared Python contract used by every backend workstream.
- `backend/app/services/email_forensics/` parses messages and extracts immutable evidence without executing or fetching anything.
- `backend/app/services/detection/` produces explainable content-based findings; email text is data, never system instruction.
- `backend/app/services/threat_intel/` enriches indicators and preserves `UNKNOWN` when providers fail or have no data.
- `backend/app/services/geolocation/` describes observed public email infrastructure only. It never claims to locate an attacker or sender physically.
- `backend/app/services/risk/` converts normalized signals into a deterministic, versioned 0–100 score.
- `backend/app/services/orchestrator/` coordinates the layers without embedding their feature logic.
- `backend/app/services/reporting/` defines report generation over a completed analysis.
- `backend/app/api/`, `backend/app/core/`, and `backend/app/db/` are reserved for transport, configuration/security, and persistence.
- `docs/contracts/openapi.yaml` is the transport contract, and `docs/contracts/sample_analysis.json` is a cross-team example payload.
- `frontend/` is reserved for the React/TypeScript/Vite/Tailwind application and is intentionally empty.

### Trust boundaries

Uploads are size-limited and validated before parsing. Original names are metadata only, attachments are never executed, URLs are never automatically visited, and untrusted HTML is never directly rendered. External providers are optional failure domains: their timeouts or errors become warnings/unknown results and must not abort the core forensic analysis. Secrets are environment-only configuration and must be redacted from logs and reports.

### Controlled demo mode

`DEMO_MODE=false` is the default. Setting `DEMO_MODE=true` explicitly replaces only threat-intelligence and observed-infrastructure geolocation providers with deterministic synthetic adapters. Their provider identity contains `DEMO-SYNTHETIC (not live verified)`, and the analysis is marked `PARTIAL` with a demo warning. Email parsing, MIME processing, metadata, hashes, deterministic detection, deterministic risk, persistence, reports, and evidence export remain real. Demo mode never executes attachments, visits indicators, uploads attachment content, or performs attacker attribution.

### API surface

The v1 contract defines synchronous analysis creation, case listing/retrieval, PDF report retrieval, and health status:

- `POST /api/v1/cases/analyze`
- `GET /api/v1/cases`
- `GET /api/v1/cases/{case_id}`
- `GET /api/v1/cases/{case_id}/report`
- `GET /api/v1/health`

See `docs/contracts/openapi.yaml` for request/response details. Implementation, dependency selection, migrations, and local run commands are intentionally deferred.
