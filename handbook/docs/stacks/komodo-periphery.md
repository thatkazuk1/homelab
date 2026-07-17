# komodo-periphery

Custom Komodo Periphery agent (sops + age baked in) enabling `sops exec-env` secret decryption at deploy time. Deployed and updated manually per host — not Komodo-managed itself (bootstrap circularity: Komodo can't manage the agent that runs Komodo's per-host connection).

## Reference

| Field | Value |
|---|---|
| Category | meta-infra |
| Status | meta-infra |
| Repo path | [`stacks/komodo-periphery/`](https://github.com/meetKazuki/homelab/tree/master/stacks/komodo-periphery) |

## Deployed on

This stack runs a per-host instance on the following hosts:

- `core-01` — [compose file](https://github.com/meetKazuki/homelab/blob/master/stacks/komodo-periphery/compose.core-01.yml)
- `docker-prod-01` — [compose file](https://github.com/meetKazuki/homelab/blob/master/stacks/komodo-periphery/compose.docker-prod-01.yml)
- `garage-prod-01` — [compose file](https://github.com/meetKazuki/homelab/blob/master/stacks/komodo-periphery/compose.garage-prod-01.yml)
- `nas-01` — [compose file](https://github.com/meetKazuki/homelab/blob/master/stacks/komodo-periphery/compose.nas-01.yml)
- `plane-prod-01` — [compose file](https://github.com/meetKazuki/homelab/blob/master/stacks/komodo-periphery/compose.plane-prod-01.yml)
- `proxy-prod-01` — [compose file](https://github.com/meetKazuki/homelab/blob/master/stacks/komodo-periphery/compose.proxy-prod-01.yml)
- `telemetry-prod-01` — [compose file](https://github.com/meetKazuki/homelab/blob/master/stacks/komodo-periphery/compose.telemetry-prod-01.yml)

## Services

### `periphery`

- **Image:** `forgejo.ts.kazuki.uk/shokunbi/komodo-periphery-sops:2`
- **Container:** `komodo-periphery`
- **Restart policy:** `unless-stopped`
- **Ports:** `8120:8120`

## Secrets

No SOPS-encrypted secrets file. Configuration lives in the compose file directly or in bind-mounted files on the host.

## Related decisions

- [ADR-0005](../decisions/0005-sops-in-periphery.md)

## Operational notes

No operational notes have been added for this stack yet. To add operational context, quirks, or lessons learned, create `stacks/komodo-periphery/notes.md`. Content is composed into this section on regeneration.

---

*This page is auto-generated from `stacks/komodo-periphery/compose.<host>.yml`. Reference-level content (services, images, secrets pattern) reflects the first compose file's current state (compose.core-01.yml); per-host divergence is not rendered — see the linked files under "Deployed on" for exact per-host config. Manual edits to this page will be overwritten on next generation. To change reference content, edit the compose files. To add operational context, edit `stacks/komodo-periphery/notes.md`.*
