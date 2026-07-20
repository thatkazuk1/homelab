# qbittorrent

qBittorrent torrent client routed entirely through Gluetun's VPN tunnel (network_mode: service:gluetun) for IP isolation.

## Reference

| Field | Value |
|---|---|
| Host | `nas-01` |
| Category | download |
| Status | adopted |
| Repo path | [`stacks/qbittorrent/`](https://github.com/meetKazuki/homelab/tree/master/stacks/qbittorrent) |

## Services

### `gluetun`

- **Image:** `qmcgaw/gluetun`
- **Container:** `gluetun`
- **Restart policy:** `unless-stopped`
- **Ports:** `8000:8000`, `8000:8000/tcp`, `8080:8080`, `8388:8388/tcp`, `8388:8388/udp`, `8888:8888/tcp`, `8999:8999/tcp`, `8999:8999/udp`

### `qbittorrent`

- **Image:** `lscr.io/linuxserver/qbittorrent:latest`
- **Container:** `qbittorrent`
- **Restart policy:** `unless-stopped`
- **Network mode:** `service:gluetun`

## Named volumes

- `gluetun-data`

## Secrets

This stack uses the [SOPS-encrypted secrets pattern](../decisions/0010-per-stack-sops-secrets.md). Encrypted values live in `stacks/qbittorrent/secrets.enc.env`; the Komodo compose wrapper decrypts them into environment variables at deploy time.

## Related decisions

- [ADR-0010](../decisions/0010-per-stack-sops-secrets.md)

## Operational notes

No operational notes have been added for this stack yet. To add operational context, quirks, or lessons learned, create `stacks/qbittorrent/notes.md`. Content is composed into this section on regeneration.

---

*This page is auto-generated from `stacks/qbittorrent/compose.yml`. Reference-level content (host, services, images, secrets pattern) reflects the compose file's current state. Manual edits to this page will be overwritten on next generation. To change reference content, edit the compose file. To add operational context, edit `stacks/qbittorrent/notes.md`.*
