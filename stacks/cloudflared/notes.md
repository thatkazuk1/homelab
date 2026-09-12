- The `secrets.enc.env` vars (`PUID`, `PGID`, `TZ`) are trivial — none are actually sensitive,
  included for uniformity with every other adopted stack. The real credentials — an Argo
  Tunnel origin certificate (`cert.pem`) and a `<uuid>.json` credentials file
  (`TunnelID`/`TunnelSecret`/`AccountTag`) — stay host-side under
  `/opt/homelab/cloudflared/config/`, bind-mounted, never committed to git. This is the
  classic named-tunnel model, not the newer token-based one.
- Each redeploy causes the tunnel to briefly drop and reconnect (a few seconds of
  interruption across every `*.kazuki.uk` route it carries) — expected, not a fault.

## Two tunnels, one stack directory

As of 2026-09-12 this stack carries **two independent tunnels**, one per host, sharing this
one directory and the one `secrets.enc.env` (same pattern as `hawser`):

- `compose.docker-prod-01.yml` — the original fleet tunnel, `nexus-pve-main`. Carries every
  fleet-infra `*.kazuki.uk` hostname (plex, jellyfin, komodo, forgejo, etc.) plus whatever
  Coolify-tenant hostnames haven't yet been migrated to the personal tunnel below.
- `compose.coolify-prod-01.yml` — a second, dedicated tunnel, `coolify-prod-01` (tunnel ID
  `eb941ef0-32b1-4120-9b05-3cb11a4bb501`), running on `coolify-prod-01` itself. Exists purely
  to isolate personal-project ingress from the fleet tunnel's blast radius — restarting one
  no longer bounces the other's hostnames. Each host has its own `/opt/homelab/cloudflared/
  config/` directory (own `config.yml`, own credentials JSON); nothing is shared between the
  two except this repo's compose/secrets files.
- Started empty (`ingress: [{service: http_status:404}]` only) — no hostnames migrated yet.
  Adding a personal-project hostname here means editing `coolify-prod-01`'s `config.yml`
  directly (SSH, backup-first, same discipline as the fleet tunnel) and creating the matching
  Cloudflare DNS record (operator action, proxied CNAME → `eb941ef0-32b1-4120-9b05-3cb11a4bb501.cfargotunnel.com`).
- The origin cert used to `tunnel create` this second tunnel came from a **fresh** `cloudflared
  tunnel login` (2026-09-12) run natively (not via the fleet's Docker image) — the fleet's old
  `cert.pem` (Nov 2025) was rejected by current `cloudflared` (2026.9.0) as invalid/expired.
  That old cert wasn't needed again after tunnel creation (`tunnel run` only needs the
  credentials JSON) and was removed from `coolify-prod-01`'s config directory as unnecessary.
