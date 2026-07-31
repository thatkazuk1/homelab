# homelab

A two-node Proxmox cluster and bare-metal fleet, managed as a single GitOps monorepo.

## Table of Contents
- [About the Project](#about-the-project)
- [Project Status](#project-status)
- [Getting Started](#getting-started)
  - [Dependencies](#dependencies)
  - [Technology Stack](#technology-stack)
  - [Third-party Services](#third-party-services)
- [Installation & Development](#installation--development)
  - [Setting Up](#setting-up)
  - [Development](#development)
  - [Testing](#testing)
- [How to Get Help](#how-to-get-help)
- [Contributing](#contributing)
- [Authors](#authors)
  - [Repo Activity](#repo-activity)

## About the Project

Every deployable thing in this homelab — Docker Compose stacks across a heterogeneous fleet,
host configuration, meta-infrastructure — is (or is becoming) declared in this repo. Git is
the source of truth; [Komodo](https://komo.do) reconciles what's actually running against
what the repo says should be running.

The project has four goals, in priority order:

1. A living, queryable wiki of the homelab infrastructure ([the handbook](https://github.com/meetKazuki/homelab/tree/master/handbook))
2. GitOps-driven declarative management — this repo → deployed reality
3. Validate the "Homelab StackDoc" visualisation project against real infrastructure
4. Publish the full setup publicly

**Canonical repo:** self-hosted Forgejo (`forgejo.ts.kazuki.uk/kazuki/homelab`), reachable only
over Tailscale. **This GitHub repo is a read-only mirror** — all real work (commits, issues,
CI) happens against the canonical repo. The mirror exists to satisfy goal 4; treat pushes,
issues, or PRs opened here as informational rather than actionable.

## Project Status

![status](https://img.shields.io/badge/status-active-brightgreen)
![git](https://img.shields.io/badge/canonical%20git-self--hosted%20Forgejo-blue)
![docs](https://img.shields.io/badge/handbook-LAN--internal%20only-lightgrey)

Actively developed. CI (lint, ADR consistency checks, generated-page drift checks) runs on
the canonical Forgejo repo's self-hosted Actions runner — it does not run against this GitHub
mirror, so no live build badge is shown here rather than a badge that would always read stale.
The [handbook](handbook/) is served internally only (`handbook.lan`, LAN/Tailscale-scoped);
its source is public here even though live serving isn't yet.

## Getting Started

### Dependencies

To work on this repo (not to run the homelab — that's what Komodo and the fleet do):

- **`git`** — the whole repo is the source of truth; every change flows through a commit and
  a push.
- **An SSH client** — to reach fleet hosts directly. Present by default on Linux/macOS.
- **[`sops`](https://github.com/getsops/sops) and [`age`](https://github.com/FiloSottile/age)** —
  needed only to read or edit a stack's encrypted secrets, not to deploy one (Komodo's
  Periphery agents carry their own copies baked into a custom image). Single static binaries,
  no package manager required.
- **`docker`** — optional, only needed to preview the handbook locally before pushing.

### Technology Stack

- **Proxmox VE** — the two-node cluster hosting most of the fleet as CTs/VMs
- **Docker / Docker Compose** — the deployment unit for every stack
- **[Komodo](https://komo.do)** — Docker-level GitOps: reconciles running containers against
  this repo
- **[Forgejo](https://forgejo.org)** — self-hosted git, container registry, and CI (Forgejo
  Actions)
- **[Ansible](https://www.ansible.com)** — host-level configuration management (Docker
  baseline, Komodo Periphery, Proxmox node post-install)
- **Traefik + [CrowdSec](https://www.crowdsec.net)** — reverse proxy and behavior-based
  intrusion prevention
- **[SOPS](https://github.com/getsops/sops) + [age](https://github.com/FiloSottile/age)** —
  per-stack secret encryption, decrypted only at deploy time
- **[Garage](https://garagehq.deuxfleurs.fr)** — self-hosted S3-compatible object storage
- **[AdGuard Home](https://adguard.com/adguard-home/overview.html)** — internal (`.lan`) DNS
  resolution
- **[Tailscale](https://tailscale.com)** — private mesh networking for tailnet-scoped services
- **[MkDocs Material](https://squidfunk.github.io/mkdocs-material/)** — the handbook
- **[Coolify](https://coolify.io)** — hosts a small set of tenants (including the handbook)
  deliberately outside Komodo/git management

### Third-party Services

- **Cloudflare** — public DNS and Tunnel for anything meant to be internet-reachable
- **Tailscale** — the private tailnet backing the `ts.kazuki.uk` DNS tier
- **Google Drive** — an offload destination for `backrest` backup archives

## Installation & Development

### Setting Up

```bash
git clone https://forgejo.ts.kazuki.uk/kazuki/homelab.git
cd homelab
```

Generate (or import) the fleet's `age` key and confirm you can read a secret:

```bash
age-keygen -o ~/.config/sops/age/keys.txt   # first-time only
sops -d stacks/<any-stack>/secrets.enc.env  # confirms sops/age are wired up
```

Per-host SSH access uses one keypair per host, pinned in `~/.ssh/config` — see the handbook's
Getting Started section for the full convention and reasoning.

### Development

The GitOps loop: edit a stack's `compose.yml` (or its `secrets.enc.env` via `sops`) and push
to `master`. A single repo-level Forgejo webhook fires a Komodo Procedure that scans every
Stack and redeploys only what actually changed — no per-stack webhook setup needed. Editing
`handbook/` and pushing auto-deploys the live handbook via its Coolify pipeline within about a
minute. See `handbook/docs/operations/` for the detailed playbooks (adopting a stack, deploy
triggers, maintaining the handbook).

Preview the handbook locally before pushing:

```bash
cd handbook
docker build -t handbook-preview . && docker run --rm -d -p 8888:80 handbook-preview
```

### Testing

There's no application test suite — this repo declares infrastructure, it doesn't ship code
in the traditional sense. What runs instead:

- **Pre-commit hooks** — regenerate handbook stack pages from `stacks/` changes, and hard-fail
  on any dangling ADR reference.
- **Forgejo Actions CI** — Ansible lint + syntax check on `ansible/**` changes, an ADR-content
  consistency check (warn-only) on `stacks/**` changes, and a check that generated handbook
  stack pages match their source compose files.
- **`mkdocs build --strict`** — the same build CI runs; a clean local build (see the Setting
  Up docker command above) is a real signal before pushing handbook changes.

## How to Get Help

This is a personal homelab, not a supported project — there's no SLA and no dedicated support
channel. The [handbook](handbook/) is the primary reference for how and why things are built
the way they are; start there.

## Contributing

Not actively seeking contributions — this is a single-operator homelab and the canonical repo
lives on self-hosted Forgejo, not here. That said, this GitHub mirror's issue tracker is a
reasonable place to flag something genuinely broken in the public material (a wrong command, a
dead link); it's checked periodically, not continuously.

**[Back to top](#table-of-contents)**

## Authors

**Desmond Edem** ([@meetKazuki](https://github.com/meetKazuki)) — sole operator and author.

### Repo Activity

TBA.
