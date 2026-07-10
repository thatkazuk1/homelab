# ADR-0005: SOPS-in-Periphery via custom image for at-deploy-time secret decryption

## Status

Accepted — 2026-07-06

## Context

Every real stack in this homelab carries secrets — database passwords, API keys, webhook
tokens. These cannot live in plaintext in the Git repo; they cannot live as Komodo Variables
(that puts them inside Komodo's own database, creating a separate secrets store to maintain
and back up); and they cannot be decrypted on a workstation at commit time and pushed
encrypted-then-plaintext depending on which host reads them.

SOPS + age was already the established secrets tool in this homelab. The pattern needed was:
commit encrypted env files to Git, decrypt at deploy time inside the Komodo deployment
pipeline, before `docker compose up` runs.

Komodo supports this via a `compose_cmd_wrapper` field on each Stack: a shell command
wrapping the compose invocation. The `sops exec-env` subcommand injects decrypted variables
as environment variables into a subprocess, where Docker Compose's `${VAR}` interpolation
picks them up. This is the correct mechanism — it avoids writing decrypted content to disk
and keeps the decryption step inside the same process that runs compose.

The obstacle: Periphery agents execute Stack deployments on their host. SOPS and age are not
present in the official upstream Periphery image, and there's no supported mechanism to
inject arbitrary binaries into a running Periphery container at runtime.

## Decision

Build and maintain a **custom Periphery image** that extends the upstream image with SOPS and
age binaries baked in. The Dockerfile lives in the homelab monorepo. The age private key is
delivered to the Periphery container via a bind mount and an environment variable pointing at
it — not via Komodo Variables or any mechanism that stores it in Komodo's own database.

## Reasoning

- **Ownership over the Dockerfile.** The alternative — using an unaffiliated third-party image
  that happens to bundle SOPS — introduces an unaudited build pipeline into a
  security-adjacent component. A homelab that stores secrets with age should not trust an
  unverified image to handle those secrets. Maintaining the Dockerfile is a small ongoing
  cost (rebuild on upstream Periphery bumps) for a meaningful reduction in supply chain risk.
- **Bind mount over Komodo Variable for the age key.** Storing the age private key as a Komodo
  Variable would put the key inside Komodo's own database state, which is backed up
  separately and may eventually be copied offsite — multiple backup locations, increasing the
  attack surface. A bind mount keeps the key on the host filesystem, accessible only to the
  Periphery container that needs it.
- **`sops exec-env` over `sops exec-file`.** `exec-env` injects decrypted variables into the
  subprocess environment directly; `exec-file` writes a decrypted file to a temp location on
  disk. The env-injection path avoids a window where decrypted secrets exist on the
  filesystem, however briefly.
- **Pattern proven before real stacks depended on it.** The full chain — encrypted file
  committed to Git, Komodo pulls the repo, Periphery runs the wrapper, `sops exec-env`
  decrypts, compose reads the resulting variable, the container receives the plaintext value
  — was confirmed end-to-end before any real stack was migrated onto it.

## Consequences

- Every Docker host running Komodo Periphery must use the custom image rather than the
  upstream one.
- The custom image must be rebuilt whenever the upstream Periphery image bumps its major
  version tag.
- SOPS and age are version-pinned in the Dockerfile for reproducibility — bumped explicitly,
  never automatically.
- The age private key must exist at the expected path on every host running the custom
  Periphery before the bind mount will succeed — a manual prerequisite for each new host.
- The custom image is pushed to this homelab's own container registry so other hosts pull a
  pre-built image rather than each building locally.

## Alternatives considered

- **Unaffiliated third-party image bundling SOPS.** Rejected — unaudited build pipeline for a
  security-adjacent component. Not evaluated further.
- **Komodo Variable for the age key.** Rejected — stores the private key in Komodo's database
  and backup chain, widening the attack surface without meaningful operational benefit over a
  bind mount.
- **`sops exec-file` wrapper.** Not chosen over `exec-env` — writes decrypted content to disk
  transiently, which `exec-env` avoids entirely.
- **Pre-decrypt secrets on a workstation before commit, push plaintext env files.** Rejected
  outright — defeats the purpose of encrypted secrets in Git entirely.

---

_Source ADR authored during Sprint 2.1. Public version adapted for this
handbook; the internal record lives in the operator's private notes._
