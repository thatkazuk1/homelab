# garage

S3-compatible object storage for the fleet.

**Host:** `garage-prod-01`
**Access:** web UI at [`garage.ts.kazuki.uk`](https://garage.ts.kazuki.uk); S3 API directly
at `192.168.50.80:3900`
**Repo:** [`stacks/garage/`](https://github.com/meetKazuki/homelab/tree/master/stacks/garage)

## What it does

[Garage](https://garage.deuxfleurs.fr/) is a lightweight, self-hosted, S3-API-compatible
object store. It backs every other stack's need for object storage — backups
([`beszel`](beszel.md)'s S3 backup target), file attachments ([`sure`](sure.md)'s
`GENERIC_S3_*` vars), and Coolify's media bucket. Bucket and key naming follow the
`<consumer>-<purpose>` convention described in [Conventions](../conventions/index.md).

## Configuration

- **Compose:** two services, `garage` (the server itself) and `webui` (an admin UI), both on
  `network_mode: host`
- **Secrets:** none in git at all — no `.env`, no `secrets.enc.env`. Garage's real
  credentials (`rpc_secret`, `admin_token`, `metrics_token`) live in a bind-mounted
  `garage.toml` (host mode `600`), the same host-side-config-file pattern
  [`cloudflared`](cloudflared.md) uses. The file itself never enters git.
- **Data:** two named volumes, `garage-meta` and `garage-data`, **with** explicit `name:`
  fields — this stack follows the new-stack convention even though it was adopted from a
  running deployment, because the original deployment already had them pinned.

## Notable

- Confirmed buckets in active use: `sure-media`, `beszel-media`, `beszel-backups`,
  `coolify-media` — each with its own scoped access key, never shared across buckets, per the
  [Conventions](../conventions/index.md) page's naming rule.
- The S3 API correctly returns `403` on unauthenticated requests — verified as the expected
  behavior (API live and enforcing auth), not a fault.
- Requests to `.ts.kazuki.uk`/`.lan` hosts from an executor session don't resolve directly;
  verification during adoption was routed through an on-network host instead. Worth knowing
  if you're scripting checks against this or any other Tailscale/LAN-only service from
  outside the tailnet.

## See also

- [`beszel`](beszel.md), [`sure`](sure.md) — consumers of Garage buckets
- [Conventions](../conventions/index.md) — bucket and S3 key naming rules
