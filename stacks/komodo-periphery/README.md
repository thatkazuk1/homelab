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
- `compose.nas-01.yml` — pre-existing (ADR-0009), own path convention
  (`/Volume1/@apps/komodo`) and age-key mount per ADR-0006's TOS exception;
  **not re-verified against live state in Sprint 3i** (no TOS browser terminal
  session available that day — re-verify next time nas-01 is touched)

`forgejo-prod-01` does **not** run Periphery yet (fleet table's "pending" is
accurate — confirmed no `/opt/homelab/komodo-periphery/` on that host as of
Sprint 3i).
