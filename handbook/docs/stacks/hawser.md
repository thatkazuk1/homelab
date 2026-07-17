# hawser

Hawser agent for Dockhand remote management. Standard mode; listens on port 2376, authenticated via TOKEN env var.

## Reference

| Field | Value |
|---|---|
| Category | orchestration |
| Status | adopted |
| Repo path | [`stacks/hawser/`](https://github.com/meetKazuki/homelab/tree/master/stacks/hawser) |

## Deployed on

This stack runs a per-host instance on the following hosts:

- `coolify-prod-01` — [compose file](https://github.com/meetKazuki/homelab/blob/master/stacks/hawser/compose.coolify-prod-01.yml)
- `core-01` — [compose file](https://github.com/meetKazuki/homelab/blob/master/stacks/hawser/compose.core-01.yml)
- `garage-prod-01` — [compose file](https://github.com/meetKazuki/homelab/blob/master/stacks/hawser/compose.garage-prod-01.yml)
- `komodo-prod-01` — [compose file](https://github.com/meetKazuki/homelab/blob/master/stacks/hawser/compose.komodo-prod-01.yml)
- `plane-prod-01` — [compose file](https://github.com/meetKazuki/homelab/blob/master/stacks/hawser/compose.plane-prod-01.yml)
- `proxy-prod-01` — [compose file](https://github.com/meetKazuki/homelab/blob/master/stacks/hawser/compose.proxy-prod-01.yml)
- `telemetry-prod-01` — [compose file](https://github.com/meetKazuki/homelab/blob/master/stacks/hawser/compose.telemetry-prod-01.yml)

## Services

### `hawser`

- **Image:** `ghcr.io/finsys/hawser:latest`
- **Container:** `hawser`
- **Restart policy:** `unless-stopped`
- **Ports:** `2376:2376`

## Secrets

This stack uses the [SOPS-encrypted secrets pattern](../decisions/0010-per-stack-sops-secrets.md). Encrypted values live in `stacks/hawser/secrets.enc.env`; the Komodo compose wrapper decrypts them into environment variables at deploy time.

## Related decisions

- [ADR-0010](../decisions/0010-per-stack-sops-secrets.md)
- ADR-0014 (not yet published in the handbook — see `docs/adrs/` on disk)

## Operational notes

No operational notes have been added for this stack yet. To add operational context, quirks, or lessons learned, create `stacks/hawser/notes.md`. Content is composed into this section on regeneration.

---

*This page is auto-generated from `stacks/hawser/compose.<host>.yml`. Reference-level content (services, images, secrets pattern) reflects the first compose file's current state (compose.coolify-prod-01.yml); per-host divergence is not rendered — see the linked files under "Deployed on" for exact per-host config. Manual edits to this page will be overwritten on next generation. To change reference content, edit the compose files. To add operational context, edit `stacks/hawser/notes.md`.*
