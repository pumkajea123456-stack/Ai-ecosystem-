# ChromaCore v5 implementation status

| Layer | Status | Evidence / next action |
|---|---|---|
| Frontend | Scaffolded | UI implementation remains |
| Backend/API Gateway | Integrated | FastAPI + persistent jobs + health checks |
| PostgreSQL | Connected | Persistent job records |
| Redis | Connected | Queue and worker |
| Background Worker | Integrated | queued → processing → completed |
| Local Object Storage | Working | Local adapter; production object storage remains |
| Image inspection | Working | Pillow-backed validation |
| Semantic Vision | Pluggable | `vision_engine.py`; enable with a selected Transformers model and dependencies |
| Video inspection | Working | FFprobe-backed validation |
| Video transcoding | Implemented | FFmpeg adapter with validated codecs/formats |
| Batch Engine | Worker-backed | Queue orchestration; domain processors remain |
| MCP Server | Tool contracts | Production SDK transport/auth integration remains |
| Mobile | Client boundary | Mobile implementation remains |
| Deployment | Docker baseline | FFmpeg included; production orchestration remains |
| CI | Passing baseline | PostgreSQL + Redis + engine/API tests pass on latest validated commit |
| Production AI model | Not activated | Requires explicit model selection, weights/provider and runtime dependencies |
| Production object storage | Not configured | Requires provider and credentials |
| Billing/Marketplace/Enterprise | Not implemented | Requires business rules, auth and provider configuration |

## Current validation state

The production-step branch now contains executable media engines: Pillow image inspection, FFprobe video inspection, FFmpeg transcoding, and a configurable semantic-vision adapter. API routes expose these capabilities and contract tests cover their deterministic behavior.

Semantic inference is intentionally configuration-driven. The system must not claim detections when no model is configured. Set `CHROMACORE_VISION_BACKEND=transformers` and `CHROMACORE_VISION_MODEL=<approved-model>` and install the matching Transformers runtime before enabling inference.

## Remaining production work

1. Select and approve a semantic vision model and add its production runtime/deployment strategy.
2. Add real image object-detection/segmentation output if required by the product contract.
3. Add end-to-end video transcode tests with a generated fixture and artifact verification.
4. Replace local storage with production object storage.
5. Implement authenticated MCP transport.
6. Implement authentication/RBAC, billing, marketplace and enterprise policies.
7. Add observability, rate limits, quotas and production secrets management.
8. Run full E2E validation and merge only after the production-step CI is green.
