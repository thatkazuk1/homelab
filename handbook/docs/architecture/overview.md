# Architecture Overview

This page is the big-picture reference: what runs where, and why. It's not a tutorial —
see **Getting Started** and **Operations** for hands-on material.

## The fleet

Thirteen hosts, three tiers:

**Proxmox cluster** — two nodes, `pve-01` and `pve-02`, hosting eight guests between them:

| Host | Type | Node | Role |
|---|---|---|---|
| `docker-prod-01` | VM | `pve-01` | General-purpose Docker workloads |
| `coolify-prod-01` | CT | `pve-01` | Coolify (self-managed, not Komodo — see below) |
| `forgejo-prod-01` | CT | `pve-01` | Forgejo (git + container registry) + Actions runner |
| `telemetry-prod-01` | CT | `pve-02` | InfluxDB 3, Speedtest Tracker |
| `proxy-prod-01` | CT | `pve-02` | Traefik + CrowdSec |
| `plane-prod-01` | CT | `pve-02` | Plane (project management) |
| `garage-prod-01` | CT | `pve-02` | Garage (S3-compatible object storage) |
| `komodo-prod-01` | CT | `pve-02` | Komodo Core + FerretDB |

**Bare metal** — two standalone hosts outside the Proxmox cluster: `core-01` (Raspberry Pi 4,
arm64, runs Home Assistant among other things) and `nas-01` (TerraMaster NAS, runs the media
stack via TOS/Docker).

**Workstation** — `nexus-v`, the operator's personal machine. Not fleet infrastructure; it's
where Claude Code runs, where the age private key lives, and where all git operations
originate.

Host naming follows the `role-env-index` pattern with a few tool-identity exceptions
(`garage-prod-01`, `komodo-prod-01`, etc.) — see **Conventions** for the full rationale.

## The GitOps pipeline

```
Git (Forgejo, self-hosted, source of truth)
  │  push
  ▼
Forgejo Actions (CI, runs on forgejo-prod-01)
  │  build image
  ▼
Registry (Forgejo's private container registry, `shokunbi` org)
  │  pull
  ▼
Komodo Core (komodo-prod-01) — polls / receives webhook
  │  dispatch
  ▼
Periphery agents (one per Docker host) — reconcile running containers
  against `stacks/<name>/compose.yml` in the repo
```

Every Docker-capable host runs a Komodo Periphery agent — a custom image
(`komodo-periphery-sops`) with SOPS and age baked in, so per-stack secrets can be decrypted
at deploy time without ever touching disk in plaintext. Each stack is a directory under
`stacks/` in the monorepo; adopting a manually-run stack into this pipeline is a repeatable
playbook (see **Operations → Adopting a stack**).

**As of writing**, the Forgejo webhook is the real, working automatic redeploy trigger for
every Komodo Stack — verified live at a ~6-10 second round trip. Komodo's separate "Auto
Update" / "Poll for Updates" feature (which checks for a new image at the same tag, not a
git/compose change) isn't enabled on any current Stack; it was tried once early on and hasn't
been revisited since, not because it's broken. The handbook itself is no longer a Komodo Stack
— it moved to being a Coolify tenant, which has no auto-deploy webhook of its own, so its
publishing loop (see **Operations → Maintaining the handbook**) uses a manual Deploy click in
Coolify's UI for an unrelated reason.

## DNS tiers

Three tiers, matched to how exposed something should be:

- **`kazuki.uk`** — public, Cloudflare-fronted. Anything meant to be reachable from the open
  internet.
- **`ts.kazuki.uk`** — Tailscale-scoped. Real public DNS records, but they resolve to tailnet
  IPs — only reachable if you're on the tailnet.
- **`.lan`** — internal only, resolved via AdGuard. The default for anything without a
  specific reason to be reachable from outside the house.

Anything not explicitly behind Cloudflare Tunnel or Tailscale uses `.lan`.

## What talks to what

- **Operator (`nexus-v`)** pushes to Forgejo, which is both the git remote and the container
  registry.
- **Forgejo Actions** (a self-hosted runner, not a hosted CI service) builds images from
  pushed commits and pushes them back to Forgejo's own registry.
- **Komodo Core** watches the repo via a per-Stack Forgejo webhook and dispatches deploy
  instructions to the relevant Periphery agent. (Auto Update / Poll for Updates — a separate,
  image-tag-based trigger — exists but isn't enabled on any current Stack.)
- **Periphery agents** run on each Docker host, pull the target image from Forgejo's registry
  (using their own registry credentials — they don't inherit the SSH user's `docker login`),
  and run `docker compose` against the stack's committed compose file.
- **Traefik** (`proxy-prod-01`) fronts most `.lan` and public services — but not all; see the
  handbook's own serving setup as a documented exception below.

## What's not here

A few things are deliberately outside this picture, by choice rather than oversight:

- **`nas-01`'s media stack is not under GitOps yet.** Deferred — it runs its own Docker Compose
  stacks directly on the NAS, outside Komodo's reconciliation.
- **Home Assistant on `core-01` is manually managed, by choice.** Home Assistant's own
  configuration UI is the natural way to manage it; forcing it through GitOps compose files
  would fight the tool rather than use it.
- **Coolify (`coolify-prod-01`) runs a small set of tenants outside Komodo entirely**,
  including this repo's own StackDoc visualisation project (`infra-stackdoc-web`) and this
  handbook itself. Coolify self-upgrades and rewrites its own compose/env files independently
  of git — putting it under Komodo/git reconciliation would mean the two fight over ownership
  of the same files. Documented for the wiki goal, deliberately not Komodo-managed. See
  **Architecture → Coolify**.
- **This handbook is served by Coolify, not Komodo.** `handbook.lan` resolves to
  `coolify-prod-01`, plain HTTP, no port, no Traefik in front of it (Coolify runs its own).
  See **Architecture → Coolify** and ADR-0015 for why.
