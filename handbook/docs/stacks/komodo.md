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

This stack uses the [SOPS-encrypted secrets pattern](../decisions/0008-per-stack-sops-secrets.md). Encrypted values live in `stacks/komodo/secrets.enc.env`; the Komodo compose wrapper decrypts them into environment variables at deploy time.

## Related decisions

- [ADR-0002](../decisions/0002-komodo-for-docker-gitops.md)

## Operational notes

- Every service carries `komodo.skip` — this compose file documents the running config but
  isn't the deployment source of truth. The host still runs its own plaintext `compose.env`
  at deploy time; no `sops exec-env` wrapper is actually invoked here (bootstrap circularity:
  Komodo can't manage the compose that runs Komodo). The `secrets.enc.env` committed
  alongside it is for documentation purposes only, inert at deploy time.
- The host file `/opt/homelab/komodo/compose.yml` differs from this file: its `core` and
  `periphery` services read `env_file: ./compose.env`. Start the host stack with
  `docker compose --env-file compose.env ...` (as the host `Makefile` does), so that
  interpolation is the same. `make up` uses `--force-recreate` and restarts Core too.
- Since 2026-10-09 the `periphery` service sets `PERIPHERY_DISABLE_TERMINALS` and
  `PERIPHERY_DISABLE_CONTAINER_EXEC` to `"true"`, in an `environment:` block in the host file and
  in this file. To change only the Periphery without touching Core, run
  `docker compose --env-file compose.env up -d --no-deps periphery` in `/opt/homelab/komodo`
  (use `--dry-run` first).

---

*This page is auto-generated from `stacks/komodo/compose.yml`. Reference-level content (host, services, images, secrets pattern) reflects the compose file's current state. Manual edits to this page will be overwritten on next generation. To change reference content, edit the compose file. To add operational context, edit `stacks/komodo/notes.md`.*
