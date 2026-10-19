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

- **Image:** `artifacts.plane.so/makeplane/plane-frontend:${APP_RELEASE:-v1.4.3-rc1}`

### `space`

- **Image:** `artifacts.plane.so/makeplane/plane-space:${APP_RELEASE:-v1.4.3-rc1}`

### `admin`

- **Image:** `artifacts.plane.so/makeplane/plane-admin:${APP_RELEASE:-v1.4.3-rc1}`

### `live`

- **Image:** `artifacts.plane.so/makeplane/plane-live:${APP_RELEASE:-v1.4.3-rc1}`

### `api`

- **Image:** `artifacts.plane.so/makeplane/plane-backend:${APP_RELEASE:-v1.4.3-rc1}`

### `worker`

- **Image:** `artifacts.plane.so/makeplane/plane-backend:${APP_RELEASE:-v1.4.3-rc1}`

### `beat-worker`

- **Image:** `artifacts.plane.so/makeplane/plane-backend:${APP_RELEASE:-v1.4.3-rc1}`

### `migrator`

- **Image:** `artifacts.plane.so/makeplane/plane-backend:${APP_RELEASE:-v1.4.3-rc1}`

### `plane-db`

- **Image:** `postgres:15.19-alpine`

### `plane-redis`

- **Image:** `valkey/valkey:7.2.14-alpine`

### `plane-mq`

- **Image:** `rabbitmq:3.13.7-management-alpine`

### `plane-minio`

- **Image:** `docker.io/pgsty/minio:RELEASE.2026-08-04T00-00-00Z`

### `proxy`

- **Image:** `artifacts.plane.so/makeplane/plane-proxy:${APP_RELEASE:-v1.4.3-rc1}`
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

This stack uses the [SOPS-encrypted secrets pattern](../decisions/0008-per-stack-sops-secrets.md). Encrypted values live in `stacks/plane/secrets.enc.env`; the Komodo compose wrapper decrypts them into environment variables at deploy time.

## Related decisions

- [ADR-0008](../decisions/0008-per-stack-sops-secrets.md)

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
- `SECRET_KEY` and `LIVE_SERVER_SECRET_KEY` held Plane's public installer defaults until
  2026-10-08. On that date, both keys and the Postgres, RabbitMQ and MinIO credentials got
  new random values in `secrets.enc.env`. The compose fallback defaults still exist, but the
  secrets file overrides them. The new database credentials needed empty volumes, so the
  stack was rebuilt from nothing, and the old Plane data is gone.
- When a Komodo deploy does not create the containers (the `deploy.replicas` parser WARN,
  see Deploy triggers), deploy from inside Periphery on `plane-prod-01`:
  `docker exec -w /etc/komodo/stacks/plane/stacks/plane komodo-periphery sops exec-env secrets.enc.env 'docker compose -p plane-app up -d'`.
  The checkout is inside the Periphery container, not on the host filesystem. After a fresh
  start, the API waits until all database migrations finish. The web UI shows "Plane didn't
  start up correctly" for about two minutes.
- The image tag comes from `APP_RELEASE` (compose default in `compose.yml`). A value in
  `secrets.enc.env` overrides that default, and `sops exec-env` puts it in the environment
  before Compose runs. A pin of `v1.2.1` in the secrets file made the v1.4.2 upgrade (PR #74)
  have no effect until it was removed (2026-10-15). Do not set `APP_RELEASE` in the secrets
  file. To check the resolved tags, run `docker compose -p plane-app config` inside
  `sops exec-env` and count the `image:` lines per tag. The Plane API reports its version at
  `/api/instances/` (`instance.current_version`).
- `plane-prod-01` has a 16 GB disk. The images use about 7 GB, and Plane's own data is about
  80 MB. `plane-live` (1.7 GB) and `plane-space` (1.5 GB) are the largest images. Docker uses
  the containerd image store here, so each image exists twice: unpacked and compressed. Plan
  for about 3 GB of free space for each upgrade. Measured 2026-10-15.
- Removing an old image tag does not free its layers at once. Docker puts an 8-hour lease
  (`moby/prune.images=true`) on each removed image, so the layers stay on disk until it
  expires. `docker system df` shows these layers as reclaimable, but they share layers with
  the new tags, so the figure is too high. To free the space at once after an upgrade has been
  verified, delete only the prune leases: list them with `sudo ctr -n moby leases ls`, then
  run `sudo ctr -n moby leases delete <id>` for each ID whose label is
  `moby/prune.images=true`. Keep the leases that have no label, because they belong to
  containers and images that are in use. Check that no pull is running first.
- `minio/minio` no longer exists on Docker Hub (HTTP 404 on 2026-10-19), so every Komodo
  deploy of this stack failed at the image pull ("pull access denied for minio/minio"), even
  though the old image was still on the host. The stack now uses the community fork
  `docker.io/pgsty/minio`, pinned to a release tag, the same image that upstream Plane uses
  since v1.4.3-rc1. Komodo shows the stack as "unhealthy" while the `migrator` container has
  exited with code 0; this is normal for a one-shot job.
- `plane.kazuki.uk` is behind Cloudflare Access (2026-10-09), so a public request gets the
  Access login page first. On the LAN, AdGuard resolves the name to Traefik directly, so LAN
  requests do not go through Access.
- Adopted with its vendor-supplied multi-service topology intact, per the "don't reorganize a
  working topology mid-migration" discipline.

---

*This page is auto-generated from `stacks/plane/compose.yml`. Reference-level content (host, services, images, secrets pattern) reflects the compose file's current state. Manual edits to this page will be overwritten on next generation. To change reference content, edit the compose file. To add operational context, edit `stacks/plane/notes.md`.*
