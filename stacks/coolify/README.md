# Coolify (`coolify-prod-01`) — documented, not Komodo-managed

Sprint 3j (2026-07-11) tore down the prior Coolify install and rebuilt it greenfield, formalizing
its operational standard as ADR-0016. Coolify remains deliberately outside Komodo/git management
— see ADR-0016 and ADR-0002's amendment for the full reasoning.

## Current state

- Version: Coolify 4.1.2 (fresh install via the official installer, pinned — upgrades are a
  deliberate operator action, not auto-drift).
- Platform containers: `coolify`, `coolify-db` (Postgres 15), `coolify-redis`, `coolify-realtime`,
  `coolify-proxy` (its own Traefik v3.6, `letsencrypt` cert resolver), `coolify-sentinel`
  (monitoring agent).
- Tenants: one — `stackdoc`, deployed from `github.com/thatkazuk1/infra-stackdoc` (branch
  `master`, Dockerfile build, `web` target — a static nginx-served SPA, no environment variables),
  public at `https://stackdoc.kazuki.uk`. The prior install's other three tenants (two unnamed
  applications, one standalone Postgres 18 database) were confirmed disposable by the operator
  during Sprint 3j's discovery phase and destroyed in the teardown — not migrated, not backed up.
- Admin UI: reachable directly at `coolify-prod-01`'s LAN IP, port 8000. **Not yet
  Tailscale-scoped** (`coolify.ts.kazuki.uk`) — `coolify-prod-01` was never a Tailscale tailnet
  member; this is open follow-up work, not implemented this sprint. Not publicly reachable either
  way (no live Cloudflare Tunnel route or fleet Traefik route to it).

## Why not Komodo-managed

Coolify self-upgrades independently of git — its own mechanism rewrites `docker-compose.yml`/
`.env` on every upgrade (dated `upgrade-*.log` files accumulate at `/data/coolify/source/`).
Putting this under Komodo/git reconciliation the same way as a static stack (`plane`, `sure`,
etc.) means either the two fight over ownership of these files, or Coolify's own auto-upgrade has
to be disabled — a real behavior change to how the operator upgrades Coolify, not a decision to
make implicitly. ADR-0016 formalizes: leave Coolify's own upgrade mechanism untouched, no Komodo
Stack, ever.

## Public tenant routing

Coolify's own Traefik handles TLS and routing for public tenants directly — fleet's
`proxy-prod-01` Traefik does **not** front Coolify tenants (a real change from the prior install,
which had `coolify.kazuki.uk` and `stackdoc.kazuki.uk` both live-routed through `proxy-prod-01`).
The shared Cloudflare Tunnel's ingress rule for each public Coolify tenant hostname points
directly at `coolify-prod-01`, bypassing fleet Traefik entirely. See ADR-0016 for the full
reasoning, including two Coolify-specific quirks worth knowing before adding another tenant
(domain field needs an explicit scheme; DNS must resolve to Coolify *before* it will generate any
route at all, not just before TLS will validate).

## Files

- `source.docker-compose.yml` / `source.docker-compose.prod.yml` — Coolify's own platform
  containers, as found at `/data/coolify/source/` on `coolify-prod-01`. Snapshot predates the
  Sprint 3j rebuild; not re-captured this sprint since the platform-container shape is unchanged
  (same images, same install method).
- `proxy.docker-compose.yml` — Coolify's dedicated Traefik instance, as found at
  `/data/coolify/proxy/` on `coolify-prod-01`. Coolify writes its own dynamic routing config into
  `/data/coolify/proxy/dynamic/` per application it deploys — not captured here, changes
  per-deployment.

No secrets committed — both files reference credentials via `${VAR}` interpolation from Coolify's
own `.env`, which stays host-side, unread and untouched by this documentation pass.

## Backup

No backup mechanism exists. `/data/coolify/backups/` is present but empty — confirmed during
Sprint 3j discovery, before the teardown that would have made the question moot either way.
Deferred to a future instrumentation-driven sprint per operator direction, not solved here.

## Future work

- `coolify.ts.kazuki.uk` Tailscale-scoped admin access (needs Tailscale installed on
  `coolify-prod-01`, node approval, DNS record) — see ADR-0016 Consequences.
- Handbook migration to Coolify as a second tenant (Sprint 3k).
- Coolify backup story (future instrumentation-driven sprint).
