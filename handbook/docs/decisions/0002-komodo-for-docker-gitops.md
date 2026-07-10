# ADR-0002: Komodo for Docker-level GitOps (Application Deployment)

## Status

Accepted — 2026-06-25. Implementation deferred to Sprint 2.

## Context

The homelab's automation pipeline was deliberately split into three distinct layers during
planning, rather than reaching for one tool to cover all of them — chosen specifically to
avoid the kind of over-engineering this project has pushed back on before (an earlier
rejection of Docker Swarm mode among them):

| Layer | Job | Produces |
|---|---|---|
| Provisioning | Create new VMs/CTs on Proxmox from a definition | A booted host: networking, base OS, SSH key, hostname |
| Configuration | Bring a booted host to "ready for workloads" | Users, packages, sshd, Docker, base directory layout |
| Deployment | Reconcile running Docker stacks against what's declared in Git | Containers matching `compose.yml` definitions in the monorepo |

This ADR concerns deployment only. Provisioning (OpenTofu, conditional, deferred) and
configuration (Ansible) are separate decisions.

The homelab's actual topology at the time of this decision: no Docker Swarm, no Kubernetes —
multiple independent Docker hosts, each running its own Compose stacks.

## Decision

Use **Komodo** as the deployment tool: a Core instance on a dedicated host, **Periphery**
agents on every Docker-capable host, stacks defined in the monorepo (one directory per stack
under `stacks/`).

## Reasoning

- **Topology fit.** Komodo's model — a central core plus lightweight per-host agents, each
  agent simply executing Compose operations on its own host — matches a multi-host,
  non-clustered Docker fleet exactly. It doesn't assume Swarm or Kubernetes underneath it,
  unlike several alternatives in this space.
- **Verified current relevance, not assumed.** Given how quickly self-hosted GitOps tooling
  turns over, this wasn't taken on stale knowledge — a live check at decision time confirmed
  Komodo is the currently dominant tool for this specific shape of setup (multi-host Docker,
  no orchestrator).
- **Integrates with what's already built**, rather than introducing parallel infrastructure:
  native `ntfy` support slots into the existing alerting setup with no new plumbing; Komodo's
  own configuration ("Resource Syncs") is itself expressed as TOML in Git, so its setup
  becomes version-controlled in the same monorepo it manages rather than living as unmanaged
  UI state.
- **Avoids the bootstrapping circularity becoming a long-term problem.** The Git server itself
  runs as a Docker stack and, logically, should eventually be managed the same way every
  other stack is. It cannot be from day one — the tool that would manage it doesn't exist yet
  at the point it's first stood up. Accepted as a known, temporary gap, resolved as soon as
  Komodo exists.

## Consequences

- The Git server ships without Komodo management initially — deployed and operated manually.
  This is intentional, not an oversight.
- The gap resolves in order: Komodo Core deployed on its own host, Periphery agents rolled
  out fleet-wide, then the Git server's own stack is the first thing adopted into Komodo once
  Komodo exists — closing the circularity rather than leaving it open indefinitely.
- The first proof-of-loop migration was chosen deliberately as low-risk and immediately
  visible if something breaks, and specifically to force the open question of whether
  Periphery runs cleanly on ARM hardware on day one rather than discovering it later under
  higher stakes.

## Alternatives considered

- **Kubernetes (k3s or similar) + Flux/ArgoCD, or Docker Swarm-based GitOps** — rejected on
  the same grounds Swarm mode itself was rejected earlier in this project: these solve a
  clustering/orchestration problem this homelab does not have, at a complexity cost
  disproportionate to the actual topology.
- Other Docker-Compose-oriented tools (e.g. Portainer's own stack-from-Git features, Dockge)
  were not formally evaluated against Komodo in the planning conversation — Komodo was
  identified directly via a live check of current tooling for this specific topology and
  adopted on that basis. If Komodo's fit had turned out wrong in practice, those would have
  been the most likely tools worth a real side-by-side look before reaching for something
  heavier.

---

_Source ADR authored during Sprint 2 planning. Public version adapted for this
handbook; the internal record lives in the operator's private notes._
