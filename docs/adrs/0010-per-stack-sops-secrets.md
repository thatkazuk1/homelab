# ADR-0010: Per-stack SOPS-encrypted secrets, decrypted at deploy time

## Status

Accepted — 2026-07-08

## Context

Komodo Periphery clones the git repo into its own container-internal directory and runs
`docker compose` from there. Volume bind-mount *sources* resolve via the Docker daemon
(host-wide visibility), but `env_file:` paths are read by the compose CLI process inside
Periphery's container, which cannot see host paths like `/opt/homelab/<stack>/.env`. This
surfaced as a hard blocker during Sprint 3b's `homepage` adoption: every real redeploy
attempt failed at Komodo's config-validation stage before touching the running container.

Three options were considered:

1. **(A)** Per-stack SOPS-encrypted env files committed to the repo, decrypted at deploy
   time via the `sops exec-env` wrapper already proven in ADR-0005.
2. **(B)** Widen Periphery's mount surface to `/opt/homelab:ro` fleet-wide, so `env_file:`
   can point at host paths directly.
3. **(C)** Use Komodo's built-in Variables/Secrets feature, stored in FerretDB.

## Decision

Option A.

## Reasoning

**Rejected — B:** leaves secrets as unversioned plaintext on hosts, outside git and outside
any working backup path (Backrest is designed, not yet deployed). Breaks
disaster-recovery-from-repo. Removes secret rotation from the GitOps loop. Once working,
it would become the permanent convention by inertia — hard to walk back later.

**Rejected — C:** makes Komodo's own database the canonical secret store — unversioned,
unauditable, currently backed up only to local disk on `komodo-prod-01`. Moves secrets
*out* of git rather than into it, the opposite direction of this project's GitOps goal.

## The Standard

1. Each stack with secrets carries exactly one encrypted file: `stacks/<name>/secrets.enc.env`.
   The filename matches the existing `.sops.yaml` rule (`\.enc\.(yaml|yml|json|env)$`) — no
   rule changes required.
2. Every such Stack sets the identical wrapper: `sops exec-env secrets.enc.env
   '[[COMPOSE_COMMAND]]'`. No per-stack templating. Stacks without secrets set no wrapper.
3. Compose files enumerate secret vars as bare pass-through keys (`environment:` entries
   with no value). `env_file:` lines pointing at host paths are removed.
4. Shared credentials are duplicated per stack, deliberately — consistent with the
   one-scoped-credential-per-consumer principle. Duplication keeps sharing visible as a
   smell to fix later, rather than hiding it in a shared file.
5. No split into separate plaintext/encrypted env files per stack, even where some vars
   aren't secret. Uniformity over per-stack judgment calls.
6. Periphery's mount surface stays narrow. No `/opt/homelab` mount.
7. After a stack's conversion is verified end-to-end, the host-local `.env` is deleted
   (moved-then-deleted after a one-week tripwire window). One source of truth.

## Consequences

- The first deploy after any stack's conversion is a real container recreation (resolved
  config changes), not a no-op. Planned per-stack, with data-safety verification scaled to
  what the stack holds.
- Directly unblocks Sprint 3b.1's three conversions (`homepage`, `uptime-kuma`,
  `vaultwarden`) and is inherited as a settled pattern by Sprint 3c's TOML migration.
