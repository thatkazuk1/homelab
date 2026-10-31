# beszel-agent

Beszel monitoring agent reporting docker-prod-02 host and container metrics to the fleet's Beszel hub. The agent connects out to the hub with a per-system token, so the hub does not need to reach this host.

## Reference

| Field | Value |
|---|---|
| Category | monitoring |
| Status | new |
| Repo path | [`stacks/beszel-agent/`](https://github.com/meetKazuki/homelab/tree/master/stacks/beszel-agent) |

## Deployed on

This stack runs a per-host instance on the following hosts:

- `docker-prod-02` — [compose file](https://github.com/meetKazuki/homelab/blob/master/stacks/beszel-agent/compose.docker-prod-02.yml)
- `nas-01` — [compose file](https://github.com/meetKazuki/homelab/blob/master/stacks/beszel-agent/compose.nas-01.yml)

## Services

### `beszel-agent`

- **Image:** `henrygd/beszel-agent`
- **Container:** `beszel-agent`
- **Restart policy:** `unless-stopped`
- **Network mode:** `host`

## Named volumes

- `beszel-agent-data`

## Secrets

This stack uses the [SOPS-encrypted secrets pattern](../decisions/0008-per-stack-sops-secrets.md). Encrypted values live in `stacks/beszel-agent/secrets.enc.env`; the Komodo compose wrapper decrypts them into environment variables at deploy time.

## Related decisions

- [ADR-0008](../decisions/0008-per-stack-sops-secrets.md)

## Operational notes

No operational notes have been added for this stack yet. To add operational context, quirks, or lessons learned, create `stacks/beszel-agent/notes.md`. Content is composed into this section on regeneration.

---

*This page is auto-generated from `stacks/beszel-agent/compose.<host>.yml`. Reference-level content (services, images, secrets pattern) reflects the first compose file's current state (compose.docker-prod-02.yml); per-host divergence is not rendered — see the linked files under "Deployed on" for exact per-host config. Manual edits to this page will be overwritten on next generation. To change reference content, edit the compose files. To add operational context, edit `stacks/beszel-agent/notes.md`.*
