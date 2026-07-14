# dockhand

Self-hosted Docker management platform. Replaces Portainer as the fleet's container management UI. Manages remote hosts via Hawser agents in Standard mode.

## Reference

| Field | Value |
|---|---|
| Host | `docker-prod-01` |
| Category | orchestration |
| Status | adopted |
| Public URL | [dockhand.ts.kazuki.uk](https://dockhand.ts.kazuki.uk) |
| Repo path | [`stacks/dockhand/`](https://github.com/meetKazuki/homelab/tree/master/stacks/dockhand) |

## Services

### `dockhand`

- **Image:** `fnsys/dockhand:latest`
- **Container:** `dockhand`
- **Restart policy:** `unless-stopped`
- **Ports:** `3050:3000`

## Named volumes

- `dockhand-data`

## Secrets

No SOPS-encrypted secrets file. Configuration lives in the compose file directly or in bind-mounted files on the host.

## Related decisions

- ADR-0014 (not yet published in the handbook — see `docs/adrs/` on disk)
- ADR-0016 (not yet published in the handbook — see `docs/adrs/` on disk)

## Operational notes

## Purpose

Dockhand replaces Portainer as the fleet's Docker management UI.
Chosen for modern UX and Docker-focused feature set (Portainer's
Kubernetes/Swarm capabilities are unused on this fleet).

## Port

Host port `3050`, not Dockhand's native `3000` — port 3000 on `docker-prod-01`
is already bound by `homepage` (`0.0.0.0:3000`). Container-side port is still
`3000`. Also note: the compose binds plainly (not `127.0.0.1`-scoped) — Traefik
on `proxy-prod-01` reaches every tailnet-scoped admin UI on this fleet over the
LAN by host IP, so a loopback-only bind would make it unreachable from Traefik.
The handoff's original template used `127.0.0.1:3000:3000`, which would have
hit both problems.

## Image

`fnsys/dockhand:latest` on Docker Hub — not `ghcr.io/finsys/*`. The
handoff's original template assumed a GHCR image under the `finsys`
namespace; that path doesn't exist. Verified against the project's own
compose file and manual at deploy time (2026-07-14).

## Admin setup

No `ADMIN_PASSWORD` env var, no forced first-run wizard. Authentication
is **disabled by default** on first launch — the dashboard is reachable
with no login until an admin manually enables it via
Settings → Authentication and creates the first admin user. Since this
instance is only reachable at `dockhand.ts.kazuki.uk` (tailnet-scoped),
exposure during that window is bounded to tailnet members, but auth
should be enabled immediately after first access.

## Multi-host management

Managed hosts run Hawser agents in Standard mode (see `stacks/hawser/`).
Environments configured via Dockhand's UI (Settings → Environments).

**Local socket is not auto-detected.** Unlike Portainer, Dockhand does not
show `docker-prod-01`'s own containers by default — the handoff assumed it
would ("local Docker socket appears as the default environment"), but that's
wrong. It must be added explicitly under Settings → Environments → Add
Environment, connection type "Local socket" (same-machine, socket already
mounted — no host/port/token needed, unlike Standard Agent). Confirmed
working 2026-07-14: 13 containers visible after adding it, matching
`docker ps` count on `docker-prod-01` directly. Our container runs as root
(confirmed via `docker exec dockhand id`), so the socket-permission-denied
path the manual describes for non-root default users never applied here.

## Related decisions

Portainer retirement decided during migration to Dockhand — no ADR
opened, since replacement of one Docker-management tool with another
doesn't warrant one.

---

*This page is auto-generated from `stacks/dockhand/compose.yml`. Reference-level content (host, services, images, secrets pattern) reflects the compose file's current state. Manual edits to this page will be overwritten on next generation. To change reference content, edit the compose file. To add operational context, edit `stacks/dockhand/notes.md`.*
