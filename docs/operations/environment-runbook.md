# Test environment runbook

## Purpose

This runbook creates a repeatable local integration environment and provides checks that separate application defects from environment failures.

## Components and ports

| Component | Container port | Host exposure | Readiness check |
|---|---:|---|---|
| Gateway and QA console | 8080 | `0.0.0.0:8080` | `/health/ready` |
| Transformer | 8082 | `127.0.0.1:8082` | `/health/ready` |
| Partner simulator | 8083 | `127.0.0.1:8083` | `/health/ready` |
| Worker | n/a | none | heartbeat file in container |
| PostgreSQL | 5432 | none | `pg_isready` |

Only the gateway is intended for general host access. Diagnostic service ports bind to loopback, and the database remains inside the Compose network.

## Clean setup

```bash
cp .env.example .env
docker compose config
docker compose down --volumes --remove-orphans
docker compose up --detach --build --wait --wait-timeout 180
python scripts/wait_for_service.py http://127.0.0.1:8080/health/ready --timeout 60
```

Review `docker compose ps` before testing. Every service should be running and healthy.

## Confidence check

1. Call gateway readiness and version endpoints.
2. Reset the partner simulator with the local admin token.
3. Submit `test-data/valid/transmission-json.json`.
4. Poll status until `DELIVERED`.
5. Verify one partner attempt and one acknowledgement.
6. Confirm event history contains `QUEUED`, `PROCESSING`, and `DELIVERED`.

This check verifies routing, persistence, worker polling, transformation, delivery, and acknowledgement without exercising the whole regression pack.

## Logs and diagnostics

```bash
docker compose ps --all
docker compose logs --no-color gateway worker transformer partner-mock postgres
docker compose config > artifacts/compose-resolved.yaml
docker inspect relayhub-qa-lab-gateway-1
```

Use the message ID and correlation ID to follow one transaction. Do not add passwords, tokens, or full controlled payloads to defect tickets.

## Reset levels

- **Scenario reset:** delete partner simulator state; preserves message database.
- **Application restart:** `docker compose restart`; preserves database volume.
- **Clean baseline:** `docker compose down --volumes`, then start again.
- **Image rebuild:** add `--build --pull` when validating dependency or base-image changes.

Record the reset level in execution evidence because it changes the interpretation of persistence and recovery tests.

## Common failures

| Symptom | Check | Likely action |
|---|---|---|
| Gateway not ready | PostgreSQL health and gateway logs | restore database connectivity; do not file API defect yet |
| Message remains queued | worker health and heartbeat | inspect worker startup and DB connection |
| Message fails before partner attempt | transformer health and URL configuration | restore service or verify expected failure test |
| Partner admin returns 401 | `X-Admin-Token` and `.env` value | correct local test configuration |
| Port already allocated | `docker compose ps`, local process list | stop stale lab instance or change host mapping |
| Old data affects result | message ID and volume state | use unique test IDs or perform documented clean reset |

## Shutdown

```bash
docker compose down --remove-orphans
```

Use `--volumes` only when the stored state is no longer required as evidence.
