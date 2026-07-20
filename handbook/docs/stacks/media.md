# media

Arr-stack media automation running as one compose project on nas-01: Seerr, Aurral, FlareSolverr, Prowlarr, Radarr, Sonarr, Bazarr, Lidarr.

## Reference

| Field | Value |
|---|---|
| Host | `nas-01` |
| Category | media |
| Status | adopted |
| Repo path | [`stacks/media/`](https://github.com/meetKazuki/homelab/tree/master/stacks/media) |

## Services

### `seerr`

- **Image:** `ghcr.io/seerr-team/seerr:latest`
- **Container:** `seerr`
- **Restart policy:** `unless-stopped`
- **Ports:** `5055:5055`

### `aurral`

- **Image:** `ghcr.io/lklynet/aurral:latest`
- **Container:** `aurral`
- **Restart policy:** `unless-stopped`
- **Ports:** `3001:3001`

### `flaresolverr`

- **Image:** `ghcr.io/flaresolverr/flaresolverr:latest`
- **Container:** `flaresolverr`
- **Restart policy:** `unless-stopped`
- **Ports:** `8191:8191`

### `prowlarr`

- **Image:** `lscr.io/linuxserver/prowlarr:latest`
- **Container:** `prowlarr`
- **Restart policy:** `unless-stopped`
- **Ports:** `9696:9696`

### `radarr`

- **Image:** `lscr.io/linuxserver/radarr:latest`
- **Container:** `radarr`
- **Restart policy:** `unless-stopped`
- **Ports:** `7878:7878`

### `sonarr`

- **Image:** `lscr.io/linuxserver/sonarr:latest`
- **Container:** `sonarr`
- **Restart policy:** `unless-stopped`
- **Ports:** `8989:8989`

### `bazarr`

- **Image:** `lscr.io/linuxserver/bazarr:latest`
- **Container:** `bazarr`
- **Restart policy:** `unless-stopped`
- **Ports:** `6767:6767`

### `lidarr`

- **Image:** `lscr.io/linuxserver/lidarr:nightly`
- **Container:** `lidarr`
- **Restart policy:** `unless-stopped`
- **Ports:** `8686:8686`

## Secrets

This stack uses the [SOPS-encrypted secrets pattern](../decisions/0010-per-stack-sops-secrets.md). Encrypted values live in `stacks/media/secrets.enc.env`; the Komodo compose wrapper decrypts them into environment variables at deploy time.

## Related decisions

- [ADR-0010](../decisions/0010-per-stack-sops-secrets.md)

## Operational notes

No operational notes have been added for this stack yet. To add operational context, quirks, or lessons learned, create `stacks/media/notes.md`. Content is composed into this section on regeneration.

---

*This page is auto-generated from `stacks/media/compose.yml`. Reference-level content (host, services, images, secrets pattern) reflects the compose file's current state. Manual edits to this page will be overwritten on next generation. To change reference content, edit the compose file. To add operational context, edit `stacks/media/notes.md`.*
