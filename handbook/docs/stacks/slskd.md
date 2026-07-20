# slskd

Soulseek client with a web UI and remote-configurable API.

## Reference

| Field | Value |
|---|---|
| Host | `nas-01` |
| Category | media |
| Status | adopted |
| Repo path | [`stacks/slskd/`](https://github.com/meetKazuki/homelab/tree/master/stacks/slskd) |

## Services

### `slskd`

- **Image:** `slskd/slskd:latest`
- **Container:** `slskd`
- **Restart policy:** `unless-stopped`
- **Ports:** `5030:5030`, `5031:5031`, `50300:50300`

## Secrets

This stack uses the [SOPS-encrypted secrets pattern](../decisions/0010-per-stack-sops-secrets.md). Encrypted values live in `stacks/slskd/secrets.enc.env`; the Komodo compose wrapper decrypts them into environment variables at deploy time.

## Related decisions

- [ADR-0010](../decisions/0010-per-stack-sops-secrets.md)

## Operational notes

No operational notes have been added for this stack yet. To add operational context, quirks, or lessons learned, create `stacks/slskd/notes.md`. Content is composed into this section on regeneration.

---

*This page is auto-generated from `stacks/slskd/compose.yml`. Reference-level content (host, services, images, secrets pattern) reflects the compose file's current state. Manual edits to this page will be overwritten on next generation. To change reference content, edit the compose file. To add operational context, edit `stacks/slskd/notes.md`.*
