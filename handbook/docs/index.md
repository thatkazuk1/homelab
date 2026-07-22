# Kazuki's Homelab Handbook

This homelab runs on a two-node Proxmox cluster, a handful of bare-metal boxes (a Raspberry
Pi, a NAS), and a personal workstation — all tied together by GitOps. Every deployable thing,
from Docker Compose stacks to host configuration, is declared in a single monorepo. [Komodo](https://komo.do)
reconciles what's actually running against what the repo says should be running. [Forgejo](https://forgejo.org),
self-hosted, is the source of truth Git server behind all of it.

This handbook is the living reference for that setup — written alongside the infrastructure,
not after the fact. It's meant to answer "how does this actually work" and "why is it built
this way," for whoever's reading: a future version of the person running it, or someone else
running something similar.

## Where to go

- **Getting Started** — SSH access and the SOPS/age secrets workflow, if you're setting up to work on this repo.
- **Architecture** — the fleet, the GitOps pipeline, and what talks to what.
- **Operations** — playbooks: adopting a stack into GitOps, maintaining this handbook.
- **Conventions** — how hosts, users, buckets, and compose files are named, and why.
- **Decisions** — the architecture decision records behind the choices above.

## Work in progress

This handbook grows as the homelab grows. Some sections (a per-stack catalog, deeper
architecture diagrams) are deliberately thin right now and will fill in over future sprints.
What's here is accurate as of the date it was written — that's the standard this handbook
holds itself to over completeness.

## Elsewhere

The full source — compose files, this handbook, and everything else meant to be shared —
lives in the public repo: [github.com/meetKazuki/homelab](https://github.com/meetKazuki/homelab).

The infrastructure this handbook documents is also the validation target for
[Homelab StackDoc](https://stackdoc.kazuki.uk), a separate visualisation project.

---

_This handbook's structure and aesthetic are inspired by [Pydantic's docs](https://docs.pydantic.dev)._
