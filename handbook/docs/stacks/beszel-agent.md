# beszel-agent

Beszel monitoring agent reporting nas-01 host and container metrics to the fleet's Beszel hub.

## Reference

| Field | Value |
|---|---|
| Host | `nas-01` |
| Category | monitoring |
| Status | adopted |
| Repo path | [`stacks/beszel-agent/`](https://github.com/meetKazuki/homelab/tree/master/stacks/beszel-agent) |

## Services

### `beszel-agent`

- **Image:** `henrygd/beszel-agent`
- **Container:** `beszel-agent`
- **Restart policy:** `unless-stopped`
- **Network mode:** `host`

## Secrets

This stack uses the [SOPS-encrypted secrets pattern](../decisions/0010-per-stack-sops-secrets.md). Encrypted values live in `stacks/beszel-agent/secrets.enc.env`; the Komodo compose wrapper decrypts them into environment variables at deploy time.

## Related decisions

- [ADR-0010](../decisions/0010-per-stack-sops-secrets.md)

## Operational notes

No operational notes have been added for this stack yet. To add operational context, quirks, or lessons learned, create `stacks/beszel-agent/notes.md`. Content is composed into this section on regeneration.

---

*This page is auto-generated from `stacks/beszel-agent/compose.yml`. Reference-level content (host, services, images, secrets pattern) reflects the compose file's current state. Manual edits to this page will be overwritten on next generation. To change reference content, edit the compose file. To add operational context, edit `stacks/beszel-agent/notes.md`.*
