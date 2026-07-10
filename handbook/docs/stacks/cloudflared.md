# cloudflared

The Cloudflare Tunnel client — the on-ramp for every `kazuki.uk` public route.

**Host:** `docker-prod-01`
**Access:** not itself web-accessible; it's the egress tunnel that carries traffic for
`*.kazuki.uk` routes (e.g. [`ntfy`](ntfy.md)) to their internal services
**Repo:** [`stacks/cloudflared/`](https://github.com/meetKazuki/homelab/tree/master/stacks/cloudflared)

## What it does

`cloudflared` maintains an outbound-only connection from `docker-prod-01` to Cloudflare's
edge, so services can be reached at a public `kazuki.uk` domain without opening any inbound
port on the home network. This deployment runs the named tunnel `nexus-pve-main`.

## Configuration

- **Compose:** single-service, `cloudflare/cloudflared:latest`, runs
  `tunnel --no-autoupdate --config /etc/cloudflared/config.yml run nexus-pve-main`
- **Secrets:** ADR-0010 pattern for the trivial vars — `secrets.enc.env` carries `PUID`,
  `PGID`, `TZ` (none of which are actually sensitive; included for uniformity with every
  other adopted stack). The real credentials — an Argo Tunnel origin certificate (`cert.pem`)
  and a `<uuid>.json` credentials file (`TunnelID`/`TunnelSecret`/`AccountTag`) — stay
  host-side under `/opt/homelab/cloudflared/config/`, bind-mounted, never committed to git.
  This is the classic named-tunnel model, not the newer token-based one.
- **Data:** none beyond the config/credentials bind mount above.

## Notable

- Adopted in Sprint 3c.2. The secret surface here is a genuinely different shape than most
  ADR-0010 stacks — no env-based secret at all, just files that stay host-side by the same
  reasoning `garage`'s `garage.toml` does (bind-mount sources resolve via the Docker daemon,
  full host visibility, no need to bring them into git).
- Each redeploy causes the tunnel to briefly drop and reconnect (a few seconds of
  interruption across every `*.kazuki.uk` route it carries) — expected, not a fault.

## See also

- [`garage`](garage.md) — the other stack using the host-side-config-file secrets pattern
- [ADR-0010 Per-stack SOPS secrets](../decisions/0010-per-stack-sops-secrets.md)
