# ChromaCore v5.0

Modular image/video processing and AI vision platform scaffold based on the supplied architecture.

## Architecture

Web/Mobile -> API Gateway -> Image Engine / Video Engine / Batch Engine / AI Vision / Marketplace / Billing / MCP / Enterprise

## Stack

- Backend: FastAPI + PostgreSQL + Redis + background workers + object storage
- Frontend: React/Vite-ready scaffold
- AI Vision: OpenCV/Python service boundary
- MCP: tool definitions for image, video, scene analysis, presets and batch jobs
- Deployment: Docker Compose baseline

## API

- POST `/v5/process-image`
- POST `/v5/process-video`
- POST `/v5/batch-process`
- POST `/v5/analyze-scene`
- POST `/v5/generate-preset`
- GET `/v5/account`
- GET `/v5/usage`

## Status

This is the first executable source package. It intentionally uses deterministic/mock processing where external model or object-storage credentials are not configured, so the API can be started and tested without fabricating production integrations.
