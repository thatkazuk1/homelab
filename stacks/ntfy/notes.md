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
