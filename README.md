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

See `docs/contracts/openapi.yaml` for request/response details.

## Docker Compose

The existing FastAPI application and TanStack/Vite frontend can run together without adding another database:

```bash
docker compose build
docker compose up
```

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- Backend health: `http://localhost:8000/api/v1/health`

Compose uses the existing SQLite configuration with a single named volume by default. Copy `.env.example` to an untracked `.env` only when overrides are needed; set `DOCKER_DATABASE_URL` there to use the application's existing PostgreSQL/Supabase configuration. Provider credentials remain optional environment variables and are never passed to image builds. For a browser running on another host, set the public, non-secret `VITE_API_BASE_URL` before building the frontend image.

## PostgreSQL / Supabase persistence

The backend is the only component that connects to the database. Set `DATABASE_URL` to the Supabase PostgreSQL connection string for direct or Compose-backed runs. `DOCKER_DATABASE_URL` is an optional Compose-only override, primarily for selecting the named-volume SQLite path without changing local host configuration. Standard `postgresql://` and `postgres://` URLs are normalized to the Psycopg 3 SQLAlchemy driver. Keep the database password in the deployment environment or secret manager; never expose it through `VITE_*` variables.

Apply migrations before starting a PostgreSQL deployment:

```bash
python -m alembic -c backend/alembic.ini upgrade head
```

The API does not create PostgreSQL tables at startup. Local and automated-test SQLite databases retain the existing non-destructive `create_all` behavior. For an existing database that already has the `cases` table but has never been managed by Alembic, verify that its columns and indexes match the initial migration, back it up, and then run `python -m alembic -c backend/alembic.ini stamp 0001_create_cases` once instead of replaying the initial migration.

The current persistence model deliberately stores the complete `EmailAnalysis` aggregate in `cases.analysis_json` alongside searchable case summary columns. Parsed email evidence, timeline events, report inputs, and evidence-export inputs therefore persist atomically with the case. PDF reports and evidence ZIP files remain generated on demand; there are no existing report, export, or analyst metadata entities requiring separate tables.
