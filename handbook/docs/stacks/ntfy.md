# ntfy

A self-hosted push-notification service — the fleet's alerting transport.

**Host:** `core-01`
**Access:** [`ntfy.kazuki.uk`](https://ntfy.kazuki.uk) (public, reached via the `cloudflared`
tunnel)
**Repo:** [`stacks/ntfy/`](https://github.com/meetKazuki/homelab/tree/master/stacks/ntfy)

## What it does

`ntfy` lets any service or script publish a notification to a topic, and any subscribed
client (phone, browser, another service) receives it in near-real-time. Komodo has native
`ntfy` support (see [ADR-0002](../decisions/0002-komodo-for-docker-gitops.md)), so it's the
transport for deploy/failure alerts as well as ad-hoc notifications from other stacks.

## Configuration

- **Compose:** single-service, `binwiederhier/ntfy`
- **Secrets:** none. `.env` carried `PUID`, `PGID`, `TZ`, and `NTFY_BASE_URL` — all inlined
  as literal values in the compose file, no `secrets.enc.env`, no wrapper.
- **Data:** bind mount, `/opt/homelab/ntfy/config:/var/lib/ntfy` — cache, auth, and
  attachment storage.
- **Access control:** `NTFY_AUTH_DEFAULT_ACCESS=deny-all` with `NTFY_ENABLE_LOGIN=false`
  configured, per the live compose file.

## Notable

- Adopted in Sprint 3c.1 — the first stack adoption executed by a Claude Code session rather
  than the earlier paste-relay model, and the one that established the operator-drives-UI /
  executor-drives-shell division of labor later formalized as
  [ADR-0013](../decisions/index.md).
- `PUID`/`PGID` are carried in the compose file but are inert — the `binwiederhier/ntfy` image
  doesn't do linuxserver-style UID/GID remapping, and nothing in the container actually reads
  them. Preserved anyway, for exact config parity with the pre-adoption state.
- This is also the stack that surfaced the fleet's arm64 `sops`/`age` binary bug in the custom
  Periphery image (later root-caused and fixed) — `ntfy` itself was never blocked by it, since
  it carries no real secrets.

## See also

- [Adopting a stack](../operations/adopting-a-stack.md)
- [ADR-0002 Komodo for Docker GitOps](../decisions/0002-komodo-for-docker-gitops.md)
