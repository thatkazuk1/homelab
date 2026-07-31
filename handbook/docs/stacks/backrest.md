# backrest

Centralized restic backup orchestration — backs up docker-prod-01's own stack data to Google Drive. Remote-host backup (proxy-prod-01, telemetry-prod-01, core-01) is deferred pending an architecture decision — see the sprint status report.

## Reference

| Field | Value |
|---|---|
| Host | `docker-prod-01` |
| Category | backup |
| Status | adopted |
| Public URL | [backrest.ts.kazuki.uk](https://backrest.ts.kazuki.uk) |
| Repo path | [`stacks/backrest/`](https://github.com/meetKazuki/homelab/tree/master/stacks/backrest) |

## Services

### `backrest`

- **Image:** `ghcr.io/garethgeorge/backrest:v1.14.1`
- **Container:** `backrest`
- **Restart policy:** `unless-stopped`
- **Ports:** `9898:9898`

## Named volumes

- `beszel_data`
- `sure_app_storage`
- `sure_postgres_data`

## Secrets

This stack uses the [SOPS-encrypted secrets pattern](../decisions/0010-per-stack-sops-secrets.md). Encrypted values live in `stacks/backrest/secrets.enc.env`; the Komodo compose wrapper decrypts them into environment variables at deploy time.

## Related decisions

- ADR-0010 (not yet published in the handbook — see `docs/adrs/` on disk)

## Operational notes

No operational notes have been added for this stack yet. To add operational context, quirks, or lessons learned, create `stacks/backrest/notes.md`. Content is composed into this section on regeneration.

---

*This page is auto-generated from `stacks/backrest/compose.yml`. Reference-level content (host, services, images, secrets pattern) reflects the compose file's current state. Manual edits to this page will be overwritten on next generation. To change reference content, edit the compose file. To add operational context, edit `stacks/backrest/notes.md`.*
