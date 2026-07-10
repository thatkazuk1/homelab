# ADR-0011: Flat stack layout — `stacks/<name>/`, not `stacks/<host>/<name>/`

## Status

Accepted — 2026-07-08

## Context

An earlier adoption informally settled on a flat repo layout (`stacks/<name>/compose.yml`)
without a documented decision, while adopting the fleet's first real stack. This formalizes
that precedent before a mechanical wave of further adoptions begins, so later work has a
documented convention to follow rather than an implicit one.

A Komodo Stack's host binding lives in its `Server` field, which is mutable in the Komodo UI
— moving a stack to a different host is a UI change, not a file move. Nesting the repo path
by host (`stacks/<host>/<name>/`) would imply a coupling between git structure and host
assignment that Komodo's data model doesn't actually have.

## Decision

Flat layout: `stacks/<name>/compose.yml`. Host stays out of the path entirely.

Where per-host variants of the *same* stack genuinely diverge — the Periphery agent's own
compose file is the current example — the host goes in the **filename**, not a directory
level: `<host>.compose.yml`, not `<stack>/<host>/compose.yml`.

## Reasoning

Host-nesting would encode a fact (which host runs this stack) in a place that isn't the
source of truth for that fact (Komodo's `Server` field is). Keeping the path flat avoids a
directory rename every time a stack is reassigned to a different server, and avoids the git
history noise that would come with it.

## Consequences

- No existing stacks needed retroactive restructuring — this formalized what was already in
  place.
- Every subsequent stack adoption inherited this convention as one of its settled patterns,
  alongside [ADR-0010](0010-per-stack-sops-secrets.md)'s secrets standard.

## Alternatives considered

- **`stacks/<host>/<name>/`** — the layout implicitly assumed before this decision. Rejected
  because it couples the git path to a fact (host assignment) that Komodo already tracks
  authoritatively elsewhere, creating two sources of truth for the same information.

---

_Source ADR authored during Sprint 3b.1. Public version adapted for this
handbook; the internal record lives in the operator's private notes._
