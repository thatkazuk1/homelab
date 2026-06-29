# ADR-0004: FerretDB over MongoDB as Komodo's database backend

## Status

Accepted — 2026-06-29

## Context

Komodo Core requires a MongoDB-wire-protocol-compatible database. Sprint 2 needed to pick a backend before Komodo Core could be deployed on `komodo-prod-01`.

The default, best-documented option is real MongoDB. It's also the path of least resistance: every Komodo install guide assumes it, and it's a known quantity operationally.

This was weighed against the FOSS-alignment principle already established in ADR-0001 (Forgejo over Gitea): MongoDB moved to the SSPL license in 2018, which is not OSI-approved and has been the direct cause of multiple open-source projects forking away from it. Running it would mean accepting the same kind of licensing posture this homelab's tooling choices have otherwise deliberately avoided.

## Decision

Use **FerretDB v2**, backed by PostgreSQL with the DocumentDB extension, instead of MongoDB.

## Reasoning

- **License.** FerretDB is Apache 2.0. PostgreSQL and the DocumentDB extension are both permissively licensed. No SSPL exposure anywhere in the stack.
- **Standardization.** This homelab already runs Postgres elsewhere (Jellystat, Sure Finance). Adding another Postgres-backed service is less new surface area than introducing MongoDB as a one-off dependency solely for Komodo.
- **Resource footprint.** FerretDB 2.x's DocumentDB-extension architecture is reported to run lighter than a full MongoDB instance for workloads of this size — relevant on a homelab CT with modest allocated resources.
- **Official support path.** Komodo ships an official `ferretdb.compose.yaml` template alongside its MongoDB one — this isn't an unsupported workaround, it's a maintained first-class deployment option.

## Accepted tradeoff

FerretDB v2 is materially less travelled than MongoDB as a Komodo backend. This was flagged as a risk going into Sprint 2, and execution validated that concern directly rather than leaving it theoretical:

- The official compose template ships with **no version pin** on the `postgres-documentdb` and `ferretdb` images — contrary to Komodo's own in-template warning to pin versions, and contrary to this homelab's standing convention everywhere else. Had to be fixed manually post-deploy by capturing the resolved tags after first boot rather than trusting a pre-verified pin, because public version-compatibility information for the FerretDB/DocumentDB pairing was found to be inconsistent across sources at the time of writing.
- First boot produced a transient `connection refused` between Komodo Core/FerretDB and Postgres — Postgres takes longer to complete `initdb` + extension loading than the compose file's `depends_on` (container-start-only, no health-condition gating) accounts for. Recovered automatically via container restart policy, but it's a rough edge a MongoDB deployment wouldn't have presented.
- Community documentation and discussion volume for FerretDB-as-Komodo's-backend is a fraction of what's available for the MongoDB path — confirmed while researching the above two issues, where MongoDB-backend troubleshooting threads vastly outnumber FerretDB ones.

None of this was a blocker. All of it is now known and documented rather than discovered cold during a future incident.

## Alternatives considered

- **MongoDB (the default path).** Rejected on licensing grounds per the above — same FOSS-alignment reasoning already applied to the Forgejo/Gitea decision in ADR-0001.
- **SQLite.** Not viable — Komodo's database layer expects a MongoDB-wire-protocol backend; SQLite is not a supported option for this deployment mode.
