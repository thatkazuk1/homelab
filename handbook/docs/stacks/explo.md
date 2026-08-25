# explo

Generates weekly/monthly/daily discovery playlists from ListenBrainz recommendations, downloading singles via slskd into music/explo/ and creating matching playlists in Navidrome. Configured via its own first-run web setup wizard, not env vars.

## Reference

| Field | Value |
|---|---|
| Host | `nas-01` |
| Category | media |
| Status | adopted |
| Repo path | [`stacks/explo/`](https://github.com/meetKazuki/homelab/tree/master/stacks/explo) |

## Services

### `explo`

- **Image:** `ghcr.io/lumepart/explo:latest`
- **Container:** `explo`
- **Restart policy:** `unless-stopped`
- **Ports:** `7288:7288`

## Secrets

This stack uses the [SOPS-encrypted secrets pattern](../decisions/0008-per-stack-sops-secrets.md). Encrypted values live in `stacks/explo/secrets.enc.env`; the Komodo compose wrapper decrypts them into environment variables at deploy time.

## Related decisions

- [ADR-0008](../decisions/0008-per-stack-sops-secrets.md)

## Operational notes

No operational notes have been added for this stack yet. To add operational context, quirks, or lessons learned, create `stacks/explo/notes.md`. Content is composed into this section on regeneration.

---

*This page is auto-generated from `stacks/explo/compose.yml`. Reference-level content (host, services, images, secrets pattern) reflects the compose file's current state. Manual edits to this page will be overwritten on next generation. To change reference content, edit the compose file. To add operational context, edit `stacks/explo/notes.md`.*
