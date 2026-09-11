# kinboard

Kinboard — self-hosted family "kitchen wall planner" (calendars, shopping, meals, chores, pocket money) on a bundled self-hosted Supabase (Postgres + Kong + GoTrue + Realtime + PostgREST + Storage) backend. Adopted from the vendor's own multi-container bundle; go2rtc (camera streaming) and the optional integrations (weather, Google Calendar, Immich, Bring!, SMTP) are dropped from this deployment — none were requested, and Kinboard's own docs mark them as independently addable later with no compose change beyond re-adding the relevant env vars.

## Reference

| Field | Value |
|---|---|
| Host | `docker-prod-02` |
| Category | applications |
| Status | new |
| Public URL | [planner.kazuki.uk](https://planner.kazuki.uk) |
| Repo path | [`stacks/kinboard/`](https://github.com/meetKazuki/homelab/tree/master/stacks/kinboard) |

## Services

### `db`

- **Image:** `supabase/postgres:15.14.1.159`
- **Container:** `kinboard-db`
- **Restart policy:** `unless-stopped`

### `db-init`

- **Image:** `supabase/postgres:15.14.1.159`
- **Container:** `kinboard-db-init`
- **Restart policy:** `no`

### `kong`

- **Image:** `kong:3.9.3`
- **Container:** `kinboard-kong`
- **Restart policy:** `unless-stopped`
- **Ports:** `8100:8000`

### `auth`

- **Image:** `supabase/gotrue:v2.189.0`
- **Container:** `kinboard-auth`
- **Restart policy:** `unless-stopped`

### `realtime`

- **Image:** `supabase/realtime:v2.102.3`
- **Container:** `kinboard-realtime`
- **Restart policy:** `unless-stopped`

### `rest`

- **Image:** `postgrest/postgrest:v14.16`
- **Container:** `kinboard-rest`
- **Restart policy:** `unless-stopped`

### `storage`

- **Image:** `supabase/storage-api:v1.60.4`
- **Container:** `kinboard-storage`
- **Restart policy:** `unless-stopped`

### `imgproxy`

- **Image:** `darthsim/imgproxy:v4.0.12`
- **Container:** `kinboard-imgproxy`
- **Restart policy:** `unless-stopped`

### `webapp`

- **Image:** `ghcr.io/svenger87/kinboard:latest@sha256:64d150dac9c0c564a215dfa76c5f42d28f802d8e49a583c5fb62356bb0135a6b`
- **Container:** `kinboard-webapp`
- **Restart policy:** `unless-stopped`
- **Ports:** `3001:3000`

### `cron`

- **Image:** `mcuadros/ofelia@sha256:efcbe2c5cf658a25de6443c1462d653f9cc03791d642e01fc6c638a00f97e492`
- **Container:** `kinboard-cron`
- **Restart policy:** `unless-stopped`

## Secrets

This stack uses the [SOPS-encrypted secrets pattern](../decisions/0008-per-stack-sops-secrets.md). Encrypted values live in `stacks/kinboard/secrets.enc.env`; the Komodo compose wrapper decrypts them into environment variables at deploy time.

## Related decisions

- [ADR-0008](../decisions/0008-per-stack-sops-secrets.md)

## Operational notes

No operational notes have been added for this stack yet. To add operational context, quirks, or lessons learned, create `stacks/kinboard/notes.md`. Content is composed into this section on regeneration.

---

*This page is auto-generated from `stacks/kinboard/compose.yml`. Reference-level content (host, services, images, secrets pattern) reflects the compose file's current state. Manual edits to this page will be overwritten on next generation. To change reference content, edit the compose file. To add operational context, edit `stacks/kinboard/notes.md`.*
