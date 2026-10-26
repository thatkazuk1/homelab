# recyclarr

Recyclarr syncs the TRaSH Guides anime quality profiles and custom formats into Sonarr and Radarr once a day. The profile settings live in recyclarr.yml in this folder.

## Reference

| Field | Value |
|---|---|
| Host | `nas-01` |
| Category | media |
| Status | new |
| Repo path | [`stacks/recyclarr/`](https://github.com/meetKazuki/homelab/tree/master/stacks/recyclarr) |

## Services

### `recyclarr`

- **Image:** `ghcr.io/recyclarr/recyclarr:8.8.0`
- **Container:** `recyclarr`
- **Restart policy:** `unless-stopped`

## Named volumes

- `recyclarr-config`

## Secrets

This stack uses the [SOPS-encrypted secrets pattern](../decisions/0008-per-stack-sops-secrets.md). Encrypted values live in `stacks/recyclarr/secrets.enc.env`; the Komodo compose wrapper decrypts them into environment variables at deploy time.

## Related decisions

- [ADR-0008](../decisions/0008-per-stack-sops-secrets.md)

## Operational notes

No operational notes have been added for this stack yet. To add operational context, quirks, or lessons learned, create `stacks/recyclarr/notes.md`. Content is composed into this section on regeneration.

---

*This page is auto-generated from `stacks/recyclarr/compose.yml`. Reference-level content (host, services, images, secrets pattern) reflects the compose file's current state. Manual edits to this page will be overwritten on next generation. To change reference content, edit the compose file. To add operational context, edit `stacks/recyclarr/notes.md`.*
