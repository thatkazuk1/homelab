# Custom Komodo Periphery image

Adds `sops` + `age` to the official `ghcr.io/moghtech/komodo-periphery` image so
Komodo Stacks can use `compose_cmd_wrapper = "sops exec-env ..."` for at-deploy-time
secret decryption.

## Build

```bash
docker build \
  --build-arg PERIPHERY_VERSION=2 \
  --build-arg SOPS_VERSION=3.13.1 \
  --build-arg AGE_VERSION=1.3.1 \
  -t komodo-periphery-sops:2 \
  .
```

## Upstream version tracking

Bump `PERIPHERY_VERSION` when the official Periphery releases. Rebuild and redeploy.

## Sprint 3 follow-up

Push to Forgejo's container registry once that registry is configured, so other
hosts can pull rather than each building locally.

## Terminals and container exec are disabled

The goal: `PERIPHERY_DISABLE_TERMINALS=true` on every host, and also
`PERIPHERY_DISABLE_CONTAINER_EXEC=true` on `docker-prod-01` and `forgejo-prod-01`. Then Komodo
Core cannot open a shell on a host or in a container, and a stolen Komodo API key or Core
session cannot give a direct shell. Use SSH for shell work.

History, so that the same mistake does not happen again:

- 2026-10-08: a commit set these values in the files in this directory only. The files do not
  deploy (see "How these files reach hosts" below), so no running host changed. The text here
  then said "disabled on every host", which was wrong.
- 2026-10-09: each host's own `/opt/homelab/komodo-periphery/compose.yml` was edited in place and
  the container was recreated. The Ansible template and the host vars of `docker-prod-01` and
  `forgejo-prod-01` now write the same values, so a role run does not revert them.

To check a host, `grep` its own compose file, not the file in this directory:
`ssh <host> "grep -n PERIPHERY_DISABLE /opt/homelab/komodo-periphery/compose.yml"`.

These settings affect only Komodo's UI and API. A `docker exec` on the host itself, for
example `docker exec komodo-periphery ...`, still works.

## Per-host compose tracking

There is one compose file for each host (`compose.<host>.yml`). Each file has a header
comment, an `x-meta` block and a copy of the host file. The host file is
`/opt/homelab/komodo-periphery/compose.yml`. The copy was compared with the live host files
on 2026-10-09. Only the header comment and the `x-meta` block are not on the host.

| File | Difference from the standard Ansible-templated shape |
|---|---|
| `compose.proxy-prod-01.yml`, `compose.telemetry-prod-01.yml`, `compose.plane-prod-01.yml`, `compose.docker-prod-02.yml`, `compose.coolify-prod-01.yml` | None. List-style `environment:`, `PERIPHERY_CORE_PUBLIC_KEYS=${PERIPHERY_CORE_PUBLIC_KEYS}`, `DOCKER_CONFIG` and a `docker-config` mount. |
| `compose.garage-prod-01.yml` | `PERIPHERY_CORE_PUBLIC_KEYS` is a literal value, not a `${VAR}` reference. It is the public verification key of Komodo Core, not a credential. |
| `compose.docker-prod-01.yml` | `env_file: .env` and `PERIPHERY_DISABLE_CONTAINER_EXEC=true`. |
| `compose.forgejo-prod-01.yml` | `PERIPHERY_DISABLE_CONTAINER_EXEC=true`. Komodo registers this server through `komodo/resources/default.toml`. |
| `compose.core-01.yml` | The `komodo.skip` label. No `DOCKER_CONFIG` variable and no `docker-config` mount, so this host has no Docker Hub login. |
| `compose.nas-01.yml` | Own path convention (`/Volume1/@apps/komodo`) and age key mount (ADR-0006, TOS exception). **Not compared with the live host on 2026-10-09**, because SSH to `nas-01` was not available. |

`komodo-prod-01` has no file here. Its Periphery is a service in the Komodo Core compose
project (`/opt/homelab/komodo/compose.yml`), which is a different setup.

## How these files reach hosts

Nothing applies these files automatically. They document the running state. Komodo does not
manage Periphery, and `deploy-all-changed` does not read this directory. Two methods change a host:

- The Ansible `periphery` role templates `/opt/homelab/komodo-periphery/compose.yml`.
- An operator edits `/opt/homelab/komodo-periphery/compose.yml` on the host and runs
  `docker compose up -d`.

A change to a file here does not change a running host. After a host change, update the file
here so that it matches the host file. For the 8 hosts that the Ansible `periphery` role manages
(all hosts here except `core-01` and `nas-01`), the role template renders the host file byte for
byte (checked 2026-10-09).

**Warning:** do not copy a file from this directory over a host file. The `x-meta` block and
the header comment are not on the host. Copy only the compose body, which starts at the line
`name: komodo-periphery`. `compose.forgejo-prod-01.yml` is the only exact copy of its host file.
