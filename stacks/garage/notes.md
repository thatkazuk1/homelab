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
