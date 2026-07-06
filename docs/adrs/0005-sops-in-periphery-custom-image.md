# ADR-0005: SOPS-in-Periphery via custom image for at-deploy-time secret decryption

## Status

Accepted — 2026-07-06

## Context

Sprint 3 will migrate real stacks into Komodo-managed deployments. Every real stack in
this homelab carries secrets — database passwords, API keys, webhook tokens. These cannot
live in plaintext in the Git repo; they cannot live as Komodo Variables (that puts them
inside Komodo's own database, creating a separate secrets store to maintain and back up);
and they cannot be decrypted on `nexus-v` at commit time and pushed encrypted-then-plaintext
depending on which host reads them.

SOPS + age is already the established secrets tool in this homelab (ADR implicit in Sprint 1).
The pattern needed was: commit encrypted env files to Git, decrypt at deploy time inside the
Komodo deployment pipeline, before `docker compose up` runs.

Komodo supports this via a `compose_cmd_wrapper` field on each Stack: a shell command
wrapping the compose invocation. The `sops exec-env` subcommand injects decrypted variables
as environment variables into a subprocess, where Docker Compose's `${VAR}` interpolation
picks them up. This is the correct mechanism — it avoids writing decrypted content to disk
and keeps the decryption step inside the same process that runs compose.

The obstacle: Periphery agents execute Stack deployments on their host. SOPS and age are not
present in the official `ghcr.io/moghtech/komodo-periphery` image. There is no supported
mechanism to inject arbitrary binaries into a running Periphery container at runtime.

## Decision

Build and maintain a **custom Periphery image** (`komodo-periphery-sops`) that extends the
upstream image with SOPS and age binaries baked in. The Dockerfile lives in the homelab
monorepo at `stacks/komodo-periphery/Dockerfile`. The age private key is delivered to the
Periphery container via a bind mount (`/home/kazuki/.config/sops/age/keys.txt`) and the
`SOPS_AGE_KEY_FILE` environment variable — not via Komodo Variables or any mechanism that
stores it in Komodo's database.

## Reasoning

- **Ownership over the Dockerfile.** The alternative — using an unaffiliated third-party
  DockerHub image that happens to bundle SOPS — introduces an unaudited build pipeline into
  a security-adjacent component. A homelab that stores secrets with age should not trust an
  unverified image to handle those secrets. Maintaining the Dockerfile ourselves is a small
  ongoing cost (rebuild on upstream Periphery bumps) for a meaningful reduction in supply
  chain risk.
- **Bind mount over Komodo Variable for the age key.** Storing the age private key as a
  Komodo Variable would put the key inside FerretDB's state, which is already backed up to
  `/opt/homelab/komodo/backups` and may eventually be copied offsite. The key would then
  exist in multiple backup locations, increasing the attack surface. A bind mount keeps the
  key on the host filesystem under `kazuki`-owned `600` permissions, accessible only to
  the Periphery container that needs it.
- **`sops exec-env` over `sops exec-file`.** `exec-env` injects decrypted variables into
  the subprocess environment directly; `exec-file` writes a decrypted file to a temp
  location on disk. The env-injection path avoids a window where decrypted secrets exist
  on the filesystem, however briefly.
- **Pattern proven before Sprint 3.** Sprint 2.1 validated the full chain:
  `secrets.enc.env` committed to Git → Komodo pulls repo → Periphery runs wrapper →
  `sops exec-env` decrypts → compose reads `${SECRET_MESSAGE}` → container receives
  plaintext value. End-to-end confirmed on `docker-prod-01` before any real stack depends
  on it.

## Consequences

- Every Docker host that runs Komodo Periphery must use the custom image rather than the
  upstream one. Sprint 2.1 deploys this to `docker-prod-01` only; Sprint 3 propagates it
  to remaining hosts as Periphery rollout continues.
- The custom image must be rebuilt whenever the upstream Periphery image bumps its major
  version tag. The `PERIPHERY_VERSION` build arg and the image tag (`komodo-periphery-sops:N`)
  are intentionally kept in sync with the upstream major tag for traceability.
- SOPS and age are version-pinned in the Dockerfile (`SOPS_VERSION`, `AGE_VERSION`) for
  reproducibility. These must be bumped explicitly — they will not auto-update.
- The age private key must exist at `/home/kazuki/.config/sops/age/keys.txt` on every host
  running the custom Periphery before the bind mount will succeed. This is a manual
  prerequisite for each new host adoption in Sprint 3.
- **Sprint 3 follow-up:** The current build process requires SSH access to `docker-prod-01`
  and a manual `git clone` + `docker build`. Once Forgejo's container registry is configured
  (Sprint 3 first task), the custom image should be pushed there so other hosts pull a
  pre-built image rather than each building locally.

## Alternatives considered

- **Unaffiliated third-party DockerHub image bundling SOPS.** Rejected — unaudited build
  pipeline for a security-adjacent component. Not evaluated further.
- **Komodo Variable for the age key.** Rejected — stores the private key in Komodo's
  database and backup chain, widening the attack surface without meaningful operational
  benefit over a bind mount.
- **`sops exec-file` wrapper.** Not chosen over `exec-env` — writes decrypted content to
  disk transiently, which `exec-env` avoids entirely.
- **Pre-decrypt secrets on `nexus-v` before commit, push plaintext env files.** Rejected
  outright — defeats the purpose of encrypted secrets in Git entirely.
