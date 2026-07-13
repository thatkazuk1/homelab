# komodo

Komodo Core, the GitOps reconciliation engine for the fleet's Docker stacks, plus its FerretDB/Postgres backing store — the tool that turns this repo into deployed reality.

## Reference

| Field | Value |
|---|---|
| Host | `komodo-prod-01` |
| Category | meta-infra |
| Status | meta-infra |
| Public URL | [komodo.ts.kazuki.uk](https://komodo.ts.kazuki.uk) |
| Repo path | [`stacks/komodo/`](https://github.com/meetKazuki/homelab/tree/master/stacks/komodo) |

## Services

### `core`

- **Image:** `ghcr.io/moghtech/komodo-core:${COMPOSE_KOMODO_IMAGE_TAG:-2}`
- **Restart policy:** `unless-stopped`
- **Ports:** `9120:9120`

### `periphery`

- **Image:** `ghcr.io/moghtech/komodo-periphery:${COMPOSE_KOMODO_IMAGE_TAG:-2}`
- **Restart policy:** `unless-stopped`

### `postgres`

- **Image:** `ghcr.io/ferretdb/postgres-documentdb:15-0.107.0-ferretdb-2.7.0`
- **Restart policy:** `unless-stopped`

### `ferretdb`

- **Image:** `ghcr.io/ferretdb/ferretdb:2.7.0`
- **Restart policy:** `unless-stopped`

## Named volumes

- `ferretdb-state`
- `keys`
- `postgres-data`

## Secrets

This stack uses the [SOPS-encrypted secrets pattern](../decisions/0010-per-stack-sops-secrets.md). Encrypted values live in `stacks/komodo/secrets.enc.env`; the Komodo compose wrapper decrypts them into environment variables at deploy time.

## Related decisions

- [ADR-0002](../decisions/0002-komodo-for-docker-gitops.md)

## Operational notes

- Every service carries `komodo.skip` — this compose file documents the running config but
  isn't the deployment source of truth. The host still runs its own plaintext `compose.env`
  at deploy time; no `sops exec-env` wrapper is actually invoked here (bootstrap circularity:
  Komodo can't manage the compose that runs Komodo). The `secrets.enc.env` committed
  alongside it is for documentation purposes only, inert at deploy time.

---

*This page is auto-generated from `stacks/komodo/compose.yml`. Reference-level content (host, services, images, secrets pattern) reflects the compose file's current state. Manual edits to this page will be overwritten on next generation. To change reference content, edit the compose file. To add operational context, edit `stacks/komodo/notes.md`.*
