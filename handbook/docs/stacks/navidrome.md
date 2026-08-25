# navidrome

Navidrome music server (Subsonic/OpenSubsonic API) serving the shared music library on nas-01, read-only. Paired with Lidarr (stacks/media) for acquisition and any Subsonic-compatible client (e.g. Symfonium) for playback.

## Reference

| Field | Value |
|---|---|
| Host | `nas-01` |
| Category | media |
| Status | adopted |
| Repo path | [`stacks/navidrome/`](https://github.com/meetKazuki/homelab/tree/master/stacks/navidrome) |

## Services

### `navidrome`

- **Image:** `deluan/navidrome:latest`
- **Container:** `navidrome`
- **Restart policy:** `unless-stopped`
- **Ports:** `4533:4533`

## Secrets

No SOPS-encrypted secrets file. Configuration lives in the compose file directly or in bind-mounted files on the host.

## Related decisions

- [ADR-0008](../decisions/0008-per-stack-sops-secrets.md)

## Operational notes

No operational notes have been added for this stack yet. To add operational context, quirks, or lessons learned, create `stacks/navidrome/notes.md`. Content is composed into this section on regeneration.

---

*This page is auto-generated from `stacks/navidrome/compose.yml`. Reference-level content (host, services, images, secrets pattern) reflects the compose file's current state. Manual edits to this page will be overwritten on next generation. To change reference content, edit the compose file. To add operational context, edit `stacks/navidrome/notes.md`.*
