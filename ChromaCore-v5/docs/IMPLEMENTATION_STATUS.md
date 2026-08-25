# ChromaCore v5 implementation status

| Layer | Status | Evidence |
|---|---|---|
| Frontend | Scaffolded | `frontend/README.md` |
| Backend/API Gateway | Executable scaffold | `backend/app/main.py` |
| AI Vision | Service boundary | `ai_vision/README.md` |
| Video Engine | Service boundary | `video_engine/README.md` |
| Batch Engine | Queue boundary | `batch_engine/README.md` |
| MCP Server | Tool contracts | `mcp_server/server.py` |
| Mobile | Client boundary | `mobile/README.md` |
| Database | Persistence boundary | `database/README.md` |
| Deployment | Docker Compose baseline | `deployment/docker-compose.yml` |
| Production AI models | Not configured | Requires model selection/weights/API credentials |
| Production object storage | Not configured | Requires provider and credentials |
| Billing/Marketplace/Enterprise | Interface not implemented | Requires business rules and provider configuration |

## Validation sequence

1. Install `backend/requirements.txt`.
2. Run `pytest backend/tests`.
3. Run `uvicorn app.main:app --app-dir backend --reload`.
4. Verify `/health`, `/v5/account`, `/v5/usage`.
5. Exercise image/video upload and batch/preset endpoints.
6. Only after smoke tests pass, attach PostgreSQL/Redis workers and production model adapters.
