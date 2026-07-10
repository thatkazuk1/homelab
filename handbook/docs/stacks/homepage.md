# homepage

A single-page dashboard showing the state of every service in the homelab.
The first page you land on when checking whether anything's broken.

**Host:** `docker-prod-01`
**Access:** [`home.ts.kazuki.uk`](https://home.ts.kazuki.uk)
**Repo:** [`stacks/homepage/`](https://github.com/meetKazuki/homelab/tree/master/stacks/homepage)

## What it does

Homepage renders a widget dashboard from a static YAML configuration —
service tiles that call each service's own API and display live state
(container status, disk usage, request counts, etc.). Everything on the
dashboard is a service running elsewhere on the fleet; Homepage itself
just aggregates and displays.

## Configuration

- **Compose:** single-service, `ghcr.io/gethomepage/homepage`
- **Widget config:** bind-mounted from `/opt/homelab/homepage/config/`
  (plus `assets/icons` and `assets/images`)
- **Secrets:** ADR-0010 pattern — `secrets.enc.env` decrypted at deploy time
  via `sops exec-env` wrapper. Close to 40 environment variables, almost all
  API tokens/credentials for the other services Homepage's widgets call
  against (Proxmox, OPNsense, AdGuard, Tailscale, Cloudflare, CrowdSec,
  Portainer, Beszel, Speedtest Tracker, the arr-stack, and more).
- **Data:** no persistent state; the widget config file is the source of truth

## Notable

- Was the first stack adopted into Komodo (Sprint 3b.1), and the reference
  case for the whole adoption pattern — its ~40-variable secret surface
  turned out to be the largest blast radius of any stack adopted to date,
  larger than Vaultwarden's.
- Widget failures are silent — a service's widget going blank usually
  means that service is unreachable, not that Homepage is broken.
- One known casing oddity in the secrets file, `HOMEPAGE_VAR_K8s_API_KEY`,
  breaks the fleet's all-caps naming convention. Left as-is; not confirmed
  whether it causes a resolution mismatch against the widget config.

## See also

- [Adopting a stack](../operations/adopting-a-stack.md) — the pattern this
  stack established
- [ADR-0010 Per-stack SOPS secrets](../decisions/0010-per-stack-sops-secrets.md)
