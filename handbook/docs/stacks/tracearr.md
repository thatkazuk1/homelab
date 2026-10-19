# tracearr

Tracearr — playback and session monitor for the Jellyfin server on nas-01 (live sessions, watch history, transcode and bandwidth analytics, sharing detection). Runs next to Jellystat for a three-day observation period, then replaces it. Follows the vendor's standard PostgreSQL 18 compose file (TimescaleDB HA + Redis), with memory caps because nas-01 has little RAM. Jellyfin pushes events to it through the Tracearr SSE plugin.

## Reference

| Field | Value |
|---|---|
| Host | `nas-01` |
| Category | media |
| Status | new |
| Repo path | [`stacks/tracearr/`](https://github.com/meetKazuki/homelab/tree/master/stacks/tracearr) |

## Services

### `tracearr`

- **Image:** `ghcr.io/connorgallopo/tracearr:latest`
- **Container:** `tracearr`
- **Restart policy:** `unless-stopped`
- **Ports:** `3002:3000`

### `timescale`

- **Image:** `timescale/timescaledb-ha:pg18.4-ts2.29.1`
- **Container:** `tracearr-db`
- **Restart policy:** `unless-stopped`

### `redis`

- **Image:** `redis:8-alpine`
- **Container:** `tracearr-redis`
- **Restart policy:** `unless-stopped`

## Named volumes

- `redis_data`
- `timescale_data`
- `tracearr_backups`
- `tracearr_images`

## Secrets

This stack uses the [SOPS-encrypted secrets pattern](../decisions/0008-per-stack-sops-secrets.md). Encrypted values live in `stacks/tracearr/secrets.enc.env`; the Komodo compose wrapper decrypts them into environment variables at deploy time.

## Related decisions

- [ADR-0008](../decisions/0008-per-stack-sops-secrets.md)

## Operational notes

No operational notes have been added for this stack yet. To add operational context, quirks, or lessons learned, create `stacks/tracearr/notes.md`. Content is composed into this section on regeneration.

---

*This page is auto-generated from `stacks/tracearr/compose.yml`. Reference-level content (host, services, images, secrets pattern) reflects the compose file's current state. Manual edits to this page will be overwritten on next generation. To change reference content, edit the compose file. To add operational context, edit `stacks/tracearr/notes.md`.*
