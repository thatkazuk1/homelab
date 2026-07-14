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

## Related decisions

Portainer retirement decided during migration to Dockhand — no ADR
opened, since replacement of one Docker-management tool with another
doesn't warrant one.
