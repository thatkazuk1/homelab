# dossier

Dossier — self-hosted job-search tool (one profile, tailored resume and cover letter for each job, application tracking). One Next.js app that prints PDFs with Chromium, plus a Postgres database. Upstream: https://github.com/AienTech/dossier

## Reference

| Field | Value |
|---|---|
| Host | `docker-prod-02` |
| Category | applications |
| Status | new |
| Public URL | [dossier.ts.kazuki.uk](https://dossier.ts.kazuki.uk) |
| Repo path | [`stacks/dossier/`](https://github.com/meetKazuki/homelab/tree/master/stacks/dossier) |

## Services

### `dossier-db`

- **Image:** `postgres:18.3-alpine`
- **Container:** `dossier-db`
- **Restart policy:** `unless-stopped`

### `dossier`

- **Image:** `ghcr.io/aientech/dossier:v1.9.2`
- **Container:** `dossier`
- **Restart policy:** `unless-stopped`
- **Ports:** `3005:3000`

## Named volumes

- `dossier-data`
- `dossier-pgdata`

## Secrets

This stack uses the [SOPS-encrypted secrets pattern](../decisions/0008-per-stack-sops-secrets.md). Encrypted values live in `stacks/dossier/secrets.enc.env`; the Komodo compose wrapper decrypts them into environment variables at deploy time.

## Related decisions

- [ADR-0008](../decisions/0008-per-stack-sops-secrets.md)

## Operational notes

No operational notes have been added for this stack yet. To add operational context, quirks, or lessons learned, create `stacks/dossier/notes.md`. Content is composed into this section on regeneration.

---

*This page is auto-generated from `stacks/dossier/compose.yml`. Reference-level content (host, services, images, secrets pattern) reflects the compose file's current state. Manual edits to this page will be overwritten on next generation. To change reference content, edit the compose file. To add operational context, edit `stacks/dossier/notes.md`.*
