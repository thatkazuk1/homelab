# Coolify (`coolify-prod-01`) — documented, not Komodo-managed

Sprint 3c.4 discovery found Coolify actively running real workloads (not the sunset candidate
originally assumed): its own platform containers (`coolify`, `coolify-db`, `coolify-redis`,
`coolify-realtime`, `coolify-sentinel`, `coolify-proxy`), plus three Coolify-deployed
applications/databases with real running state:

- `kjwgh2nb5bv5t2xuudo2r988` — `ghcr.io/meetkazuki/infra-stackdoc-web:latest` (this repo's own
  "Homelab StackDoc" visualisation project, goal 3)
- `c8c86si9kfc4jwvnt76oxjg0` — locally-built application image, no friendly name set in Coolify
- `s2ojltxaw9p0x0dxznnp1ujd` — locally-built application image, no friendly name set in Coolify
- `tduebptw2u3tlmza1r4b9gdw` — standalone Postgres 18 database resource

Operator directed adoption of the Coolify platform itself rather than the originally-planned
sunset. The compose files below are committed **for the wiki goal (documentation) only** — they
are snapshots taken 2026-07-09, not a live Komodo Stack.

## Why not Komodo-managed

Coolify self-upgrades: `/data/coolify/source/` carries ~60 dated `upgrade-*.log` files and a
rotating `.env-<timestamp>` backup on every upgrade, going back to January 2026. Its own
mechanism rewrites `docker-compose.yml`/`docker-compose.prod.yml`/`.env` independently of git,
the same class of conflict as `nas-01`'s TOS GUI silently rewriting `sshd_config`. Putting this
under Komodo/git reconciliation the same way as a static stack (`plane`, `sure`, etc.) means
either the two fight over ownership of these files, or Coolify's own auto-upgrade has to be
disabled — a real behavior change to how the operator upgrades Coolify, not a decision to make
implicitly mid-adoption.

Operator chose: document the current shape for the wiki, leave Coolify's own upgrade mechanism
untouched, no Komodo Stack created.

## Files

- `source.docker-compose.yml` / `source.docker-compose.prod.yml` — Coolify's own platform
  containers (`coolify`, `coolify-realtime`, `coolify-db`, `coolify-redis`), as found at
  `/data/coolify/source/` on `coolify-prod-01`.
- `proxy.docker-compose.yml` — Coolify's dedicated Traefik instance (`coolify-proxy`), as found
  at `/data/coolify/proxy/` on `coolify-prod-01`. Coolify writes its own dynamic routing config
  into `/data/coolify/proxy/dynamic/` per application it deploys — not captured here, changes
  per-deployment.

No secrets committed — both files already reference credentials via `${VAR}` interpolation from
Coolify's own `.env`, which stays host-side, unread and untouched by this documentation pass.

## Coolify-managed application/database migration

Not in scope for Sprint 3c.4. If any of the four workloads above are worth migrating to
Komodo-managed stacks in a future sprint, that's per-workload adoption work with its own backup
discipline — same reasoning as the original handoff's Path B/C deferral, just reached via a
different route (operator override to "adopt the platform, don't touch its tenants" rather than
"sunset was blocked by real workloads").
