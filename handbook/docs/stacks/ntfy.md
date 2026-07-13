# ntfy

Self-hosted push-notification service — the fleet's alerting transport, including native Komodo deploy/failure alerts.

## Reference

| Field | Value |
|---|---|
| Host | `core-01` |
| Category | notifications |
| Status | adopted |
| Public URL | [ntfy.kazuki.uk](https://ntfy.kazuki.uk) |
| Repo path | [`stacks/ntfy/`](https://github.com/meetKazuki/homelab/tree/master/stacks/ntfy) |

## Services

### `ntfy`

- **Image:** `binwiederhier/ntfy`
- **Container:** `ntfy`
- **Restart policy:** `unless-stopped`
- **Ports:** `8085:80`

## Secrets

No SOPS-encrypted secrets file. Configuration lives in the compose file directly or in bind-mounted files on the host.

## Related decisions

- [ADR-0002](../decisions/0002-komodo-for-docker-gitops.md)

## Operational notes

- Access control: `NTFY_AUTH_DEFAULT_ACCESS=deny-all` with `NTFY_ENABLE_LOGIN=false`
  configured, per the live compose file.
- Adopted in Sprint 3c.1 — the first stack adoption executed by a Claude Code session rather
  than the earlier paste-relay model, and the one that established the operator-drives-UI /
  executor-drives-shell division of labor later formalized as ADR-0013.
- `PUID`/`PGID` are carried in the compose file but are inert — the `binwiederhier/ntfy` image
  doesn't do linuxserver-style UID/GID remapping, and nothing in the container actually reads
  them. Preserved anyway, for exact config parity with the pre-adoption state.
- This is also the stack that surfaced the fleet's arm64 `sops`/`age` binary bug in the custom
  Periphery image (later root-caused and fixed) — `ntfy` itself was never blocked by it, since
  it carries no real secrets.

---

*This page is auto-generated from `stacks/ntfy/compose.yml`. Reference-level content (host, services, images, secrets pattern) reflects the compose file's current state. Manual edits to this page will be overwritten on next generation. To change reference content, edit the compose file. To add operational context, edit `stacks/ntfy/notes.md`.*
