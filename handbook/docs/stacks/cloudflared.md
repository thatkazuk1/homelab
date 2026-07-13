# cloudflared

The Cloudflare Tunnel client — the on-ramp for every public kazuki.uk route, reaching internal services without opening an inbound port.

## Reference

| Field | Value |
|---|---|
| Host | `docker-prod-01` |
| Category | networking |
| Status | adopted |
| Repo path | [`stacks/cloudflared/`](https://github.com/meetKazuki/homelab/tree/master/stacks/cloudflared) |

## Services

### `cloudflared-tunnel`

- **Image:** `cloudflare/cloudflared:latest`
- **Container:** `cloudflared-tunnel`
- **Restart policy:** `unless-stopped`

## Secrets

This stack uses the [SOPS-encrypted secrets pattern](../decisions/0010-per-stack-sops-secrets.md). Encrypted values live in `stacks/cloudflared/secrets.enc.env`; the Komodo compose wrapper decrypts them into environment variables at deploy time.

## Related decisions

- [ADR-0010](../decisions/0010-per-stack-sops-secrets.md)

## Operational notes

- The `secrets.enc.env` vars (`PUID`, `PGID`, `TZ`) are trivial — none are actually sensitive,
  included for uniformity with every other adopted stack. The real credentials — an Argo
  Tunnel origin certificate (`cert.pem`) and a `<uuid>.json` credentials file
  (`TunnelID`/`TunnelSecret`/`AccountTag`) — stay host-side under
  `/opt/homelab/cloudflared/config/`, bind-mounted, never committed to git. This is the
  classic named-tunnel model, not the newer token-based one.
- Each redeploy causes the tunnel to briefly drop and reconnect (a few seconds of
  interruption across every `*.kazuki.uk` route it carries) — expected, not a fault.

---

*This page is auto-generated from `stacks/cloudflared/compose.yml`. Reference-level content (host, services, images, secrets pattern) reflects the compose file's current state. Manual edits to this page will be overwritten on next generation. To change reference content, edit the compose file. To add operational context, edit `stacks/cloudflared/notes.md`.*
