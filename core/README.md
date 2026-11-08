# Autonomous Core Runtime

This directory contains the first executable foundation of the Autonomous Industrial Intelligence Core.

## Runtime contract

1. Agents produce tasks/recommendations.
2. `PolicyEngine` authorizes actions against an explicit allow-list.
3. Restricted or critical actions are denied by default.
4. Authorized execution is performed by an injected executor.
5. Every authorization and result is recorded in the audit log.

## Design boundary

The AI layer does not receive unrestricted shell, credential, financial, or industrial-control access. External integrations must be attached through narrowly scoped adapters and policies.

## Next implementation steps

- persistent PostgreSQL audit/task storage
- API service around the runtime
- queue/scheduler integration
- agent adapters
- telemetry and metrics
- test suite and CI gates
- staging/canary deployment
