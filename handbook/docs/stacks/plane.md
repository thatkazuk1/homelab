# plane

Self-hosted project management (issues, cycles, roadmaps) — a Linear/Jira-style tool.

**Host:** `plane-prod-01`
**Access:** [`plane.kazuki.uk`](https://plane.kazuki.uk) (public, Cloudflare-fronted via
Traefik on `proxy-prod-01`, forwarding to Plane's own bundled reverse proxy)
**Repo:** [`stacks/plane/`](https://github.com/meetKazuki/homelab/tree/master/stacks/plane)

## What it does

Plane is a full project-management suite, self-hosted as the vendor's own multi-container
bundle rather than a single service. It's the largest stack in the catalog by service count.

## Topology

12 services: `web`, `space`, `admin`, `live`, `api`, `worker`, `beat-worker`, `migrator`
(one-shot DB migration runner), `plane-db` (Postgres), `plane-redis`, `plane-mq` (RabbitMQ),
`plane-minio` (object storage), and a bundled `proxy` (Caddy) that terminates the app's own
routing and binds host ports 80/443 directly — Traefik on `proxy-prod-01` forwards to this
container rather than to individual services.

## Configuration

- **Compose:** vendor-supplied multi-service bundle, adopted with its structure intact per
  the "don't reorganize a working topology mid-migration" discipline.
- **Secrets:** full ADR-0010 pattern — fully env-based (no bind-mounted config files
  involved), `secrets.enc.env` covers the app, database, Redis, MinIO/S3, RabbitMQ, and proxy
  environment blocks.
- **Data:** 10 named volumes (`pgdata`, `redisdata`, `uploads`, four `logs_*` volumes,
  `rabbitmq_data`, `proxy_config`, `proxy_data`), no explicit `name:` fields — Docker's
  project-prefixed auto-generated names, preserved.

## Notable

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

## See also

- [Adopting a stack](../operations/adopting-a-stack.md)
- [ADR-0010 Per-stack SOPS secrets](../decisions/0010-per-stack-sops-secrets.md)
