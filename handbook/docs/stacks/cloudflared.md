# cloudflared

A second, dedicated Cloudflare Tunnel client for personal-project hostnames routed to Coolify — isolated from the fleet's shared tunnel (docker-prod-01) so adding or changing a personal-project route no longer bounces every kazuki.uk hostname on the fleet.

## Reference

| Field | Value |
|---|---|
| Category | networking |
| Status | adopted |
| Repo path | [`stacks/cloudflared/`](https://github.com/meetKazuki/homelab/tree/master/stacks/cloudflared) |

## Deployed on

This stack runs a per-host instance on the following hosts:

- `coolify-prod-01` — [compose file](https://github.com/meetKazuki/homelab/blob/master/stacks/cloudflared/compose.coolify-prod-01.yml)
- `docker-prod-01` — [compose file](https://github.com/meetKazuki/homelab/blob/master/stacks/cloudflared/compose.docker-prod-01.yml)

## Services

### `cloudflared-tunnel`

- **Image:** `cloudflare/cloudflared:latest`
- **Container:** `cloudflared-tunnel`
- **Restart policy:** `unless-stopped`
- **Network mode:** `host`

## Secrets

This stack uses the [SOPS-encrypted secrets pattern](../decisions/0008-per-stack-sops-secrets.md). Encrypted values live in `stacks/cloudflared/secrets.enc.env`; the Komodo compose wrapper decrypts them into environment variables at deploy time.

## Related decisions

- [ADR-0008](../decisions/0008-per-stack-sops-secrets.md)

## Operational notes

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
  fleet-infra `*.kazuki.uk` hostname (jellyfin, navidrome, ntfy, plane, etc.) and
  `status.kazuki.uk`.
- `compose.coolify-prod-01.yml` — a second, dedicated tunnel, `coolify-prod-01` (tunnel ID
  `eb941ef0-32b1-4120-9b05-3cb11a4bb501`), running on `coolify-prod-01` itself in host network
  mode. Carries the personal-project hostnames: `netwright.kazuki.uk`, `school.kazuki.uk` and the
  `oriweave.dev` names (`oriweave.dev`, `api`, `docs`, `dev`, `api-dev`, `docs-dev`). It isolates
  personal-project ingress from the fleet tunnel's blast radius — restarting one no longer
  bounces the other's hostnames. Each host has its own `/opt/homelab/cloudflared/
  config/` directory (own `config.yml`, own credentials JSON); nothing is shared between the
  two except this repo's compose/secrets files. Adding a hostname means editing that host's
  `config.yml` directly (SSH, copy first, `ingress validate`, same discipline as the fleet
  tunnel) and creating the matching Cloudflare DNS record (operator action, proxied CNAME →
  `<tunnel ID>.cfargotunnel.com`).
- **Where the main rule points.** After the gateway rollout, the main rule of every Coolify
  tenant name in **both** tunnels is `https://192.168.50.107:443` with `noTLSVerify: true`
  (fleet Traefik on `proxy-prod-01`, which runs the CrowdSec bouncer and AppSec). Fleet Traefik then
  forwards to Coolify's Traefik at `https://192.168.50.30:443`. Each name keeps a path rule
  `^/\.well-known/acme-challenge/.*` before the main rule. That rule goes straight to port 80 of
  Coolify's Traefik (`http://localhost:80` in the Coolify tunnel, `http://192.168.50.30:80` in the
  `docker-prod-01` tunnel) for the Let's Encrypt HTTP-01 challenge. Each name also needs a
  `tenant-<name>` router in `gateway/traefik/dynamic/router.yaml`. See **Architecture, Coolify**.
  The rollout runs in stages over several days, so a host file can differ from this text until
  the last stage is done.
- The origin cert used to `tunnel create` this second tunnel came from a **fresh** `cloudflared
  tunnel login` (2026-09-12) run natively (not via the fleet's Docker image) — the fleet's old
  `cert.pem` (Nov 2025) was rejected by current `cloudflared` (2026.9.0) as invalid/expired.
  That old cert wasn't needed again after tunnel creation (`tunnel run` only needs the
  credentials JSON) and was removed from `coolify-prod-01`'s config directory as unnecessary.

---

*This page is auto-generated from `stacks/cloudflared/compose.<host>.yml`. Reference-level content (services, images, secrets pattern) reflects the first compose file's current state (compose.coolify-prod-01.yml); per-host divergence is not rendered — see the linked files under "Deployed on" for exact per-host config. Manual edits to this page will be overwritten on next generation. To change reference content, edit the compose files. To add operational context, edit `stacks/cloudflared/notes.md`.*
