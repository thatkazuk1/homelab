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
  the container was recreated. The Ansible template and `docker-prod-01`'s host vars now write
  the same values, so a role run does not revert them.

To check a host, `grep` its own compose file, not the file in this directory:
`ssh <host> "grep -n PERIPHERY_DISABLE /opt/homelab/komodo-periphery/compose.yml"`.

These settings affect only Komodo's UI and API. A `docker exec` on the host itself, for
example `docker exec komodo-periphery ...`, still works.

## Per-host compose tracking (Sprint 3i)

One compose file per host (`compose.<host>.yml`), not one shared template — real
per-host drift was found during Sprint 3i's audit, so a single generic file would
misrepresent most of the fleet:

- `compose.docker-prod-01.yml` — distinct: map-style `environment:`, explicit
  `env_file: .env` container injection, `PERIPHERY_DISABLE_CONTAINER_EXEC` var
- `compose.proxy-prod-01.yml`, `compose.telemetry-prod-01.yml`,
  `compose.plane-prod-01.yml` — byte-identical to each other (modulo volume
  mount order), list-style `environment:`, `PERIPHERY_CORE_PUBLIC_KEYS=${VAR}`
- `compose.garage-prod-01.yml` — same variant, but `PERIPHERY_CORE_PUBLIC_KEYS`
  is hardcoded rather than `${VAR}`-substituted (not a credential — Komodo
  Core's public verification key)
- `compose.core-01.yml` — same variant, already `komodo.skip`-labeled on the
  host itself
- `compose.nas-01.yml` — pre-existing (ADR-0007), own path convention
  (`/Volume1/@apps/komodo`) and age-key mount per ADR-0006's TOS exception;
  **not re-verified against live state in Sprint 3i** (no TOS browser terminal
  session available that day — re-verify next time nas-01 is touched)

- `compose.forgejo-prod-01.yml` — list-style `environment:` like the standard hosts, plus
  `DOCKER_CONFIG` and a `docker-config` mount for the Docker Hub credential. Komodo registers
  this server through `komodo/resources/default.toml`.

`forgejo-prod-01` runs Periphery. The container has existed since 2026-09-25. The earlier
statement that Periphery was "pending" on this host is out of date.

## How these files reach hosts

Nothing applies these files automatically. They document the running state. Komodo does not
manage Periphery, and `deploy-all-changed` does not read this directory. Two methods change a host:

- The Ansible `periphery` role templates `/opt/homelab/komodo-periphery/compose.yml`.
- An operator copies the file from this directory to the host and runs `docker compose up -d`.

A change to a file here does not change a running host. After each change, copy the file to
the host by hand. Since 2026-10-09 the Ansible role template writes
`PERIPHERY_DISABLE_TERMINALS=true`, so a role run keeps the hardening.

**Warning:** do not copy a file from this directory over a host file. The host files have a
`DOCKER_CONFIG` line and a `docker-config` mount (a Docker Hub login) that most files here do
not have. `compose.forgejo-prod-01.yml` is the only exact copy of its host file.
