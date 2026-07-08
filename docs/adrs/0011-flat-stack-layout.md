# ADR-0011: Flat stack layout — `stacks/<name>/`, not `stacks/<host>/<name>/`

## Status

Accepted — 2026-07-08

## Context

Sprint 3b's execution thread adopted a flat repo layout (`stacks/<name>/compose.yml`)
informally, without an ADR, while adopting `homepage`. This formalizes that precedent
before Sprint 3c's mechanical TOML migration begins, so the migration has a documented
convention to follow rather than an implicit one.

A Komodo Stack's host binding lives in its `Server` field, which is mutable in the Komodo
UI — moving a stack to a different host is a UI change, not a file move. Nesting the repo
path by host (`stacks/<host>/<name>/`) would imply a coupling between git structure and
host assignment that Komodo's data model doesn't actually have.

## Decision

Flat layout: `stacks/<name>/compose.yml`. Host stays out of the path entirely.

Where per-host variants of the *same* stack genuinely diverge — `komodo-periphery` is the
current example — the host goes in the **filename**, not a directory level:
`nas-01.compose.yml`, not `komodo-periphery/nas-01/compose.yml`.

## Reasoning

Host-nesting would encode a fact (which host runs this stack) in a place that isn't the
source of truth for that fact (Komodo's `Server` field is). Keeping the path flat avoids a
directory rename every time a stack is reassigned to a different server, and avoids the
git history noise that would come with it.

## Consequences

- No existing stacks need retroactive restructuring — this formalizes what's already in
  place from Sprint 3b.
- Sprint 3c's TOML mechanical migration inherits this convention as one of its settled
  patterns, alongside ADR-0010's secrets standard.
