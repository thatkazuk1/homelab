# forgejo

Forgejo — the fleet's self-hosted git host and CI/CD Actions runner target; canonical origin for this repo, mirrored to GitHub.

## Reference

| Field | Value |
|---|---|
| Host | `forgejo-prod-01` |
| Category | meta-infra |
| Status | meta-infra |
| Public URL | [forgejo.ts.kazuki.uk](https://forgejo.ts.kazuki.uk) |
| Repo path | [`stacks/forgejo/`](https://github.com/meetKazuki/homelab/tree/master/stacks/forgejo) |

## Services

### `forgejo`

- **Image:** `codeberg.org/forgejo/forgejo:15`
- **Container:** `forgejo`
- **Restart policy:** `unless-stopped`
- **Ports:** `3000:3000`, `2222:22`

## Named volumes

- `forgejo-data`

## Secrets

No SOPS-encrypted secrets file. Configuration lives in the compose file directly or in bind-mounted files on the host.

## Related decisions

- [ADR-0001](../decisions/0001-forgejo-over-gitea.md)

## Operational notes

- The Forgejo Actions runner registers against this instance via the modern
  `server.connections` config-file mechanism — Forgejo 15's `register` CLI subcommand is
  deprecated and no longer works against this instance's registration-token API.
- The tracked compose drifted once from the live host (missing
  `FORGEJO__webhook__ALLOWED_HOST_LIST`), caught and synced during Sprint 3i's meta-infra
  audit.

---

*This page is auto-generated from `stacks/forgejo/compose.yml`. Reference-level content (host, services, images, secrets pattern) reflects the compose file's current state. Manual edits to this page will be overwritten on next generation. To change reference content, edit the compose file. To add operational context, edit `stacks/forgejo/notes.md`.*
