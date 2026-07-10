# Decisions

## What ADRs are

Architecture Decision Records: short, single-topic documents that capture a decision, the
context it was made in, the reasoning behind it, and its consequences. Written at the time
the decision is made, not reconstructed afterward — so the reasoning is contemporaneous, not
a retroactive justification.

## Why they're here

Reasoning matters as much as outcome. Anyone reading this handbook can see *what* the
infrastructure looks like just by reading the compose files and this handbook's other
sections. ADRs are for *why* — including the tradeoffs that were rejected, and the ones that
turned out to have real rough edges in practice. A homelab documented this way is worth more
to a stranger (or a future self) than one that only shows the final state.

## The list

Individual ADR pages aren't published here yet — that's future work. For now, titles and
one-line summaries:

| ADR | Decision |
|---|---|
| 0001 | Forgejo over Gitea for self-hosted git — governance and 2026 community consensus, no material technical downside |
| 0002 | Komodo for Docker-level GitOps — topology fit for a multi-host, non-clustered Docker fleet |
| 0003 | MkDocs Material for the wiki, despite entering maintenance mode — aesthetic target confirmed, risk judged bounded and revisitable |
| 0004 | FerretDB over MongoDB as Komodo's database backend — licensing (SSPL avoidance) and standardisation with existing Postgres use |
| 0005 | Custom Komodo Periphery image with SOPS + age baked in — enables at-deploy-time secret decryption without a separate secrets store |
| 0010 | Per-stack SOPS-encrypted secrets, decrypted at deploy time — one `secrets.enc.env` per stack, uniform wrapper, no plaintext on disk |
| 0011 | Flat stack layout (`stacks/<name>/`, not `stacks/<host>/<name>/`) — host binding lives in Komodo's own data model, not the git path |
| 0015 | Handbook source location and serving — source is public and tracked from day one; serving stays LAN-internal until a public-presentation decision is made |

## Which ones are public

The list above. A handful of other ADRs exist but stay operator-side, not published here:
ADRs covering fleet-internal specifics with no public-facing content (a dashboard anomaly
investigation, a per-host compose-commit decision), the reasoning behind keeping the
operator's own working notes private, the operator/executor collaboration split used during
build sprints, and a record of transcript-exposed-credential incidents and their non-rotation
rationale. None of these add value for a reader trying to understand or reproduce this setup —
they're process history, not architecture.

## When new ADRs land

Public-worthy architectural decisions get written the same way as the ones above, and land in
this section as part of whatever sprint produces them — same `stacks/` + `handbook/` workflow
as everything else meant to be shared. Individual per-ADR pages (full text, not just the
one-line summary) are planned for a future pass.
