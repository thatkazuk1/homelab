# plane

Self-hosted project management (issues, cycles, roadmaps) — a Linear/Jira-style tool, deployed as the vendor's own 12-service bundle.

## Reference

| Field | Value |
|---|---|
| Host | `plane-prod-01` |
| Category | project-management |
| Status | adopted |
| Public URL | [plane.kazuki.uk](https://plane.kazuki.uk) |
| Repo path | [`stacks/plane/`](https://github.com/meetKazuki/homelab/tree/master/stacks/plane) |

## Services

### `web`

- **Image:** `artifacts.plane.so/makeplane/plane-frontend:${APP_RELEASE:-v1.2.1}`

### `space`

- **Image:** `artifacts.plane.so/makeplane/plane-space:${APP_RELEASE:-v1.2.1}`

### `admin`

- **Image:** `artifacts.plane.so/makeplane/plane-admin:${APP_RELEASE:-v1.2.1}`

### `live`

- **Image:** `artifacts.plane.so/makeplane/plane-live:${APP_RELEASE:-v1.2.1}`

### `api`

- **Image:** `artifacts.plane.so/makeplane/plane-backend:${APP_RELEASE:-v1.2.1}`

### `worker`

- **Image:** `artifacts.plane.so/makeplane/plane-backend:${APP_RELEASE:-v1.2.1}`

### `beat-worker`

- **Image:** `artifacts.plane.so/makeplane/plane-backend:${APP_RELEASE:-v1.2.1}`

### `migrator`

- **Image:** `artifacts.plane.so/makeplane/plane-backend:${APP_RELEASE:-v1.2.1}`

### `plane-db`

- **Image:** `postgres:15.7-alpine`

### `plane-redis`

- **Image:** `valkey/valkey:7.2.11-alpine`

### `plane-mq`

- **Image:** `rabbitmq:3.13.6-management-alpine`

### `plane-minio`

- **Image:** `minio/minio:latest`

### `proxy`

- **Image:** `artifacts.plane.so/makeplane/plane-proxy:${APP_RELEASE:-v1.2.1}`
- **Ports:** `${LISTEN_HTTP_PORT:-80}:80/tcp`, `${LISTEN_HTTPS_PORT:-443}:443/tcp`

## Named volumes

- `logs_api`
- `logs_beat-worker`
- `logs_migrator`
- `logs_worker`
- `pgdata`
- `proxy_config`
- `proxy_data`
- `rabbitmq_data`
- `redisdata`
- `uploads`

## Secrets

This stack uses the [SOPS-encrypted secrets pattern](../decisions/0010-per-stack-sops-secrets.md). Encrypted values live in `stacks/plane/secrets.enc.env`; the Komodo compose wrapper decrypts them into environment variables at deploy time.

## Related decisions

- [ADR-0010](../decisions/0010-per-stack-sops-secrets.md)

## Operational notes

- The real deployment path (`/home/nexus-plane/plane/plane-app/`, compose project
  `plane-app`) diverged sharply from what was assumed going into its adoption — worth
  remembering that this repo's `stacks/plane/` directory name doesn't match the host's own
  directory structure, only Komodo's Run Directory/Project Name fields do.
- A live-but-inert secret was found during adoption: `POSTGRES_PASSWORD` didn't match what
  Postgres actually authenticated with, because the app's `DATABASE_URL` fell back to a
  hardcoded default in the vendor compose file rather than being built from the Postgres
  vars. Preserved byte-for-byte during adoption itself (never fix a landmine mid-migration),
  then fixed deliberately in a follow-up sprint once verified live against Postgres's actual
  running password.
- `SECRET_KEY` / `LIVE_SERVER_SECRET_KEY` were, as of the most recent check, still Plane's own
  public installer default values — never rotated since install. Independent of any
  transcript-exposure concern; the operator has elected to handle this at their own
  convenience.
- Adopted with its vendor-supplied multi-service topology intact, per the "don't reorganize a
  working topology mid-migration" discipline.

---

*This page is auto-generated from `stacks/plane/compose.yml`. Reference-level content (host, services, images, secrets pattern) reflects the compose file's current state. Manual edits to this page will be overwritten on next generation. To change reference content, edit the compose file. To add operational context, edit `stacks/plane/notes.md`.*
