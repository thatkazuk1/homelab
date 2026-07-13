# uptime-kuma

Uptime and status monitoring for the fleet — HTTP/TCP/ping checks across services with historical uptime data and alerting.

## Reference

| Field | Value |
|---|---|
| Host | `core-01` |
| Category | monitoring |
| Status | adopted |
| Repo path | [`stacks/uptime-kuma/`](https://github.com/meetKazuki/homelab/tree/master/stacks/uptime-kuma) |

## Services

### `uptime-kuma`

- **Image:** `louislam/uptime-kuma:2`
- **Container:** `uptime-kuma`
- **Restart policy:** `unless-stopped`
- **Network mode:** `host`

## Named volumes

- `uptime-kuma-data`

## Secrets

No SOPS-encrypted secrets file. Configuration lives in the compose file directly or in bind-mounted files on the host.

## Related decisions

- [ADR-0002](../decisions/0002-komodo-for-docker-gitops.md)

## Operational notes

- The named volume `uptime-kuma-data` is declared `external: true` — deliberately, not by
  oversight. It was live-migrated during adoption from Docker's original auto-derived name
  (`uptime-kuma_uptime-kuma-data`) to the clean explicit name, verified byte-identical before
  cutover, and marked external so Compose doesn't try to (re)create it.
- The fleet's first from-scratch Komodo adoption (Sprint 3b.1) — `uptime-kuma` was originally
  planned as the very first proof-of-loop stack (per ADR-0002) for exactly this reason: low
  risk, immediately visible if something breaks, and a chance to confirm Periphery runs
  cleanly on `core-01`'s ARM architecture early.
- A personal `Makefile` (`make up`/`down`) once sat alongside the compose file — a real risk,
  since an accidental `make up` could have silently reattached the old, un-migrated volume.
  Retired rather than reconciled.

---

*This page is auto-generated from `stacks/uptime-kuma/compose.yml`. Reference-level content (host, services, images, secrets pattern) reflects the compose file's current state. Manual edits to this page will be overwritten on next generation. To change reference content, edit the compose file. To add operational context, edit `stacks/uptime-kuma/notes.md`.*
