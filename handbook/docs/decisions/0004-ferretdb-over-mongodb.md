# ADR-0004: FerretDB over MongoDB as Komodo's database backend

## Status

Accepted — 2026-06-29

## Context

Komodo Core requires a MongoDB-wire-protocol-compatible database. A backend had to be picked
before Komodo Core could be deployed.

The default, best-documented option is real MongoDB — the path of least resistance, since
every Komodo install guide assumes it, and it's a known quantity operationally.

This was weighed against the FOSS-alignment principle already established in
[ADR-0001](0001-forgejo-over-gitea.md) (Forgejo over Gitea): MongoDB moved to the SSPL license
in 2018, which is not OSI-approved and has been the direct cause of multiple open-source
projects forking away from it. Running it would mean accepting the same kind of licensing
posture this homelab's tooling choices have otherwise deliberately avoided.

## Decision

Use **FerretDB v2**, backed by PostgreSQL with the DocumentDB extension, instead of MongoDB.

## Reasoning

- **License.** FerretDB is Apache 2.0. PostgreSQL and the DocumentDB extension are both
  permissively licensed. No SSPL exposure anywhere in the stack.
- **Standardization.** This homelab already runs Postgres elsewhere. Adding another
  Postgres-backed service is less new surface area than introducing MongoDB as a one-off
  dependency solely for Komodo.
- **Resource footprint.** FerretDB 2.x's DocumentDB-extension architecture is reported to run
  lighter than a full MongoDB instance for workloads of this size — relevant on modestly
  resourced homelab hardware.
- **Official support path.** Komodo ships an official FerretDB compose template alongside its
  MongoDB one — this isn't an unsupported workaround, it's a maintained first-class
  deployment option.

## Accepted tradeoff

FerretDB v2 is materially less travelled than MongoDB as a Komodo backend. This was flagged as
a risk going into implementation, and execution validated that concern directly rather than
leaving it theoretical:

- The official compose template shipped with **no version pin** on its Postgres/DocumentDB
  and FerretDB images — contrary to Komodo's own in-template warning to pin versions, and
  contrary to this homelab's standing convention everywhere else. Fixed manually post-deploy
  by capturing the resolved tags after first boot, because public version-compatibility
  information for the pairing was inconsistent across sources at the time.
- First boot produced a transient connection-refused error between Komodo Core/FerretDB and
  Postgres — Postgres takes longer to complete initialization than the compose file's
  container-start-only dependency ordering accounts for. Recovered automatically via restart
  policy, but a rough edge a MongoDB deployment wouldn't have presented.
- Community documentation and discussion volume for FerretDB-as-Komodo's-backend is a
  fraction of what's available for the MongoDB path.

None of this was a blocker. All of it is now known and documented rather than discovered cold
during a future incident.

## Alternatives considered

- **MongoDB (the default path).** Rejected on licensing grounds per the above — same
  FOSS-alignment reasoning already applied to the Git-server decision.
- **SQLite.** Not viable — Komodo's database layer expects a MongoDB-wire-protocol backend;
  SQLite is not a supported option for this deployment mode.

---

_Source ADR authored during Sprint 2. Public version adapted for this
handbook; the internal record lives in the operator's private notes._
