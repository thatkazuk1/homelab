# jellyfin

Jellyfin media server with Jellystat watch-history tracking (Postgres-backed), running as one compose project on nas-01.

## Reference

| Field | Value |
|---|---|
| Host | `nas-01` |
| Category | media |
| Status | adopted |
| Repo path | [`stacks/jellyfin/`](https://github.com/meetKazuki/homelab/tree/master/stacks/jellyfin) |

## Services

### `jellyfin`

- **Image:** `ghcr.io/jellyfin/jellyfin:12.0-rc2`
- **Container:** `jellyfin`
- **Restart policy:** `unless-stopped`
- **Ports:** `8096:8096`

### `jellystat`

- **Image:** `cyfershepard/jellystat:latest`
- **Container:** `jellystat`
- **Restart policy:** `unless-stopped`
- **Ports:** `3000:3000`

### `jellystat-db`

- **Image:** `postgres:15.2`
- **Container:** `jellystat-db`
- **Restart policy:** `unless-stopped`

## Secrets

This stack uses the [SOPS-encrypted secrets pattern](../decisions/0010-per-stack-sops-secrets.md). Encrypted values live in `stacks/jellyfin/secrets.enc.env`; the Komodo compose wrapper decrypts them into environment variables at deploy time.

## Related decisions

- [ADR-0010](../decisions/0010-per-stack-sops-secrets.md)

## Operational notes

No operational notes have been added for this stack yet. To add operational context, quirks, or lessons learned, create `stacks/jellyfin/notes.md`. Content is composed into this section on regeneration.

---

*This page is auto-generated from `stacks/jellyfin/compose.yml`. Reference-level content (host, services, images, secrets pattern) reflects the compose file's current state. Manual edits to this page will be overwritten on next generation. To change reference content, edit the compose file. To add operational context, edit `stacks/jellyfin/notes.md`.*
