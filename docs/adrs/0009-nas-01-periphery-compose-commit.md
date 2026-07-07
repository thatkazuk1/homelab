# ADR-0009: Commit `nas-01`'s Periphery compose file to the monorepo (Fork A)

## Status

Accepted — 2026-07-08

## Context

Sprint 3a deployed Komodo Periphery to `nas-01` (TerraMaster F4-424, TOS 7), but the
operator declined at that time to commit the resulting
`stacks/komodo-periphery/nas-01.compose.yml` to the homelab monorepo, leaving Sprint 3a's
Definition of Done partially unmet on that item. Sprint 3a.1 carried this forward as an
explicit gating decision for Sprint 3b: commit it (Fork A) or formalize a standing
exception for meta-infrastructure hosts (Fork B).

- **Fork A** — commit it. The file's only sensitive-looking field,
  `PERIPHERY_CORE_PUBLIC_KEYS`, is a public key with no secret content, so nothing
  sensitive is exposed today; anything added later goes through SOPS. Full GitOps
  coverage, disaster recovery via `git clone`.
- **Fork B** — leave it host-local, formalize Periphery/Komodo Core/Forgejo as
  meta-infrastructure with DR handled by runbook instead of git.

## Decision

Fork A. Commit `stacks/komodo-periphery/nas-01.compose.yml` to the monorepo, matching
the treatment already given to Periphery's compose files on the other seven hosts.

## Reasoning

- **Consistency.** Every other host's Periphery compose already lives in the repo;
  `nas-01` was the sole exception, an artifact of mid-sprint caution rather than a
  considered architectural stance.
- **No real secret-exposure cost.** The one field that looks sensitive is a public key
  by design — safe to commit in plaintext. It's also externalized as `${PERIPHERY_CORE_PUBLIC_KEYS}`
  rather than hardcoded, so the committed file carries no literal value at all.
- **Simpler disaster recovery.** One recovery path (`git clone` + Komodo re-registration)
  across the whole fleet, instead of git for seven hosts and a separate host-local
  runbook for the eighth.

## Consequences

- `nas-01` now follows the same GitOps coverage as the rest of the fleet — no standing
  exception to remember or explain later.
- If secrets are ever added to this compose file, they go through SOPS before commit,
  same as every other stack — no carve-out for `nas-01`.
- This ADR reverses the operator's in-the-moment Sprint 3a decision; recorded here so
  that reversal has a reason attached to it, not just a diff.
