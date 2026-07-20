# glances

System resource monitor for nas-01, exposing a web dashboard.

## Reference

| Field | Value |
|---|---|
| Host | `nas-01` |
| Category | monitoring |
| Status | adopted |
| Repo path | [`stacks/glances/`](https://github.com/meetKazuki/homelab/tree/master/stacks/glances) |

## Services

### `glances`

- **Image:** `nicolargo/glances:latest-full`
- **Container:** `glances`
- **Restart policy:** `always`
- **Network mode:** `host`

## Secrets

No SOPS-encrypted secrets file. Configuration lives in the compose file directly or in bind-mounted files on the host.

## Related decisions

- [ADR-0010](../decisions/0010-per-stack-sops-secrets.md)

## Operational notes

No operational notes have been added for this stack yet. To add operational context, quirks, or lessons learned, create `stacks/glances/notes.md`. Content is composed into this section on regeneration.

---

*This page is auto-generated from `stacks/glances/compose.yml`. Reference-level content (host, services, images, secrets pattern) reflects the compose file's current state. Manual edits to this page will be overwritten on next generation. To change reference content, edit the compose file. To add operational context, edit `stacks/glances/notes.md`.*
