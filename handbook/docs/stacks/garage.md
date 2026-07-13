# garage

S3-compatible object storage backing the fleet's backup, media, and attachment needs.

## Reference

| Field | Value |
|---|---|
| Host | `garage-prod-01` |
| Category | storage |
| Status | adopted |
| Public URL | [garage.ts.kazuki.uk](https://garage.ts.kazuki.uk) |
| Repo path | [`stacks/garage/`](https://github.com/meetKazuki/homelab/tree/master/stacks/garage) |

## Services

### `garage`

- **Image:** `dxflrs/garage:v2.2.0`
- **Container:** `garage-server`
- **Restart policy:** `unless-stopped`
- **Network mode:** `host`

### `webui`

- **Image:** `khairul169/garage-webui:1.1.0`
- **Container:** `garage-webui`
- **Restart policy:** `unless-stopped`
- **Network mode:** `host`

## Named volumes

- `garage-data`
- `garage-meta`

## Secrets

No SOPS-encrypted secrets file. Configuration lives in the compose file directly or in bind-mounted files on the host.

## Operational notes

- No secrets in git at all — no `.env`, no `secrets.enc.env`. Garage's real credentials
  (`rpc_secret`, `admin_token`, `metrics_token`) live in a bind-mounted `garage.toml` (host
  mode `600`), the same host-side-config-file pattern [cloudflared](cloudflared.md)
  uses. The file itself never enters git.
- The two named volumes **do** have explicit `name:` fields — this stack follows the
  new-stack convention even though it was adopted from a running deployment, because the
  original deployment already had them pinned.
- Confirmed buckets in active use: `sure-media`, `beszel-media`, `beszel-backups`,
  `coolify-media` — each with its own scoped access key, never shared across buckets.
- The S3 API correctly returns `403` on unauthenticated requests — verified as expected
  behavior (API live and enforcing auth), not a fault.
- Requests to `.ts.kazuki.uk`/`.lan` hosts from an executor session don't resolve directly;
  verification during adoption was routed through an on-network host instead. Worth knowing
  if you're scripting checks against this or any other Tailscale/LAN-only service from
  outside the tailnet.

---

*This page is auto-generated from `stacks/garage/compose.yml`. Reference-level content (host, services, images, secrets pattern) reflects the compose file's current state. Manual edits to this page will be overwritten on next generation. To change reference content, edit the compose file. To add operational context, edit `stacks/garage/notes.md`.*
