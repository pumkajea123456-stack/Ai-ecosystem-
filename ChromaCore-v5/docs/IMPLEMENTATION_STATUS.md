# ChromaCore v5 implementation status

| Layer | Status | Evidence / next action |
|---|---|---|
| Frontend | Scaffolded | `frontend/README.md`; UI implementation remains |
| Backend/API Gateway | Integrated | FastAPI + job lifecycle + health checks |
| PostgreSQL | Connected | Runtime schema and persistent jobs in `backend/app/db.py` |
| Redis | Connected | Queue and worker in `backend/app/worker.py` |
| Background Worker | Integrated | queued → processing → completed lifecycle |
| Local Object Storage | Working | `backend/app/storage.py`; production object storage remains |
| AI Vision | Adapter boundary | Production model/weights/API still required |
| Video Engine | Adapter boundary | Production transcoder/model still required |
| Batch Engine | Worker-backed | Processing contract is live; domain-specific processors remain |
| MCP Server | Tool contracts | SDK/server transport integration remains |
| Mobile | Client boundary | Mobile client implementation remains |
| Deployment | Docker Compose | API/worker/PostgreSQL/Redis wired |
| CI | Integration workflow added | GitHub Actions now provisions PostgreSQL + Redis and runs tests |
| Production AI models | Not configured | Requires selected model, weights or provider credentials |
| Production object storage | Not configured | Requires provider and credentials |
| Billing/Marketplace/Enterprise | Not implemented | Requires business rules, auth and provider configuration |

## Current validation state

The code has been updated to remove the previous API/test lifecycle mismatch and to connect API job creation to PostgreSQL and Redis. CI now tests the database and queue dependencies rather than testing only an isolated Python process.

A GitHub Actions run is still required to establish external CI evidence for the latest commit. No claim of CI success is made until GitHub reports a completed successful run.

## Remaining production work

1. Select and configure the real AI Vision model/provider.
2. Add real video processing/transcoding adapter.
3. Replace local storage with production object storage.
4. Implement authenticated MCP transport.
5. Implement billing, marketplace and enterprise authorization rules.
6. Add end-to-end tests for image, video and batch processing.
7. Run CI and fix any environment-specific failures before merging to `main`.
