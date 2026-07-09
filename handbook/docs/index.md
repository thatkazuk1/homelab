# Kazuki's Homelab Handbook

This is a living reference for a self-hosted, GitOps-managed homelab running on Proxmox,
Komodo, Forgejo, and Beszel. Infrastructure here is declared in Git and reconciled onto
running hosts rather than configured by hand.

Content is still being written. Sections planned:

- **Getting Started** — SSH access, SOPS/age secrets, local tooling
- **Architecture** — fleet layout, network tiers, the GitOps pipeline, naming conventions
- **Operations** — deploying a new stack, onboarding a new host, maintaining this handbook
- **Stacks** — one page per deployed service
- **Decisions** — a curated public subset of the project's architecture decisions

In the meantime, the full source — compose files, this handbook, and everything else meant
to be shared — lives in the public repo:

[github.com/meetKazuki/homelab](https://github.com/meetKazuki/homelab)

_Last built: 2026-07-10_
