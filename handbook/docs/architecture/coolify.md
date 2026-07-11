# Coolify

Coolify is the fleet's second deployment layer — a self-hosted PaaS running on
`coolify-prod-01`, sitting deliberately outside the Komodo/GitOps pipeline described in
**Architecture → Overview**. It's where tenant-shaped workloads live: things that want their
own build pipeline, their own routing, and their own pace of change, rather than a compose file
declared once and reconciled by Periphery.

## Why it's separate from Komodo

Komodo's model assumes a stack's compose file and running state are reconciled from git —
Komodo (or the operator) owns the truth, and drift gets corrected. Coolify doesn't fit that
model: it self-upgrades on its own schedule, rewriting its own `docker-compose.yml` and `.env`
independently of git every time it does. Putting Coolify itself under Komodo would mean either
the two fight over ownership of the same files, or Coolify's auto-upgrade has to be disabled —
a real behavior change, not a free abstraction. So Coolify stays a deliberate operational
island: excluded from Komodo, its own upgrade mechanism authoritative for itself, its tenants'
secrets living in its own UI/database rather than this repo's SOPS pattern. See ADR-0002 (why
Komodo exists) and ADR-0016 (Coolify's own operational standard) for the full reasoning.

The two systems aren't in tension day to day — they answer different questions. Komodo asks
"does the fleet match git?" Coolify asks "is this tenant's app running the version I told it
to build?" A workload only needs Komodo if the answer to the first question matters for it.

## How a new tenant gets deployed

Through Coolify's own UI, not a pull request against this repo:

1. **+ New → Resource**, choose a source — a git repository (public or via a connected
   account) or a plain Docker image.
2. Pick a build method. For git sources with a Dockerfile, set **Base Directory** if the
   Dockerfile isn't at the repo root (this repo's own monorepo shape needs this — see below).
3. Set a domain. Coolify's Traefik handles routing and, for public domains entered with an
   explicit `https://` scheme, obtains its own Let's Encrypt certificate — independent of
   fleet Traefik on `proxy-prod-01` entirely.
4. Deploy. Coolify builds the image, runs it, and wires up the Traefik labels itself.

No fleet-side change is required to add a tenant — that's the property ADR-0016 is built
around. The only thing that ever touches fleet Traefik is the Coolify **admin** URL itself
(`coolify.ts.kazuki.uk`), which routes through `proxy-prod-01` the same way `komodo.ts.kazuki.uk`
and `forgejo.ts.kazuki.uk` do.

## Quirks worth knowing (Coolify 4.1.2)

A few surface-level bugs and defaults, discovered across two sprints of actually using this
version, worth checking for explicitly rather than assuming they're fixed:

- **The domain field needs an explicit scheme.** A bare hostname produces a broken Traefik
  router label; enter `https://tenant.kazuki.uk` or `http://tenant.lan`, not just the
  hostname.
- **DNS must resolve *before* Coolify will create any route at all** — not just before TLS
  will validate. For a LAN-only domain, the AdGuard rewrite needs to exist first, pointed at
  `coolify-prod-01`, before the application is deployed.
- **"Ports Exposes" doesn't reliably read a Dockerfile's `EXPOSE` line.** It's defaulted to a
  generic guess (`3000`) rather than the actual exposed port on more than one deploy, causing a
  502 until corrected by hand in the app's General settings.
- **The build-time DNS validation runs from inside a container**, using the Docker daemon's
  own resolver (`/etc/docker/daemon.json`, not the host's `/etc/resolv.conf`). If that
  resolver doesn't know about `.lan` names, LAN-only domains fail validation even when the
  host itself resolves them fine.

## Handbook as a tenant

This handbook is a live example of the pattern above: deployed from the fleet monorepo's
GitHub mirror, `Base Directory` set to `/handbook` so Coolify builds only that subdirectory
against the existing `handbook/Dockerfile`, served at `http://handbook.lan/` — plain HTTP, no
port, no TLS. It replaced an earlier Komodo-Stack-plus-port-exposure setup (see ADR-0015) once
Coolify's LAN-only serving was confirmed to work cleanly.

One caveat carried over from the old pipeline: Coolify has no auto-deploy webhook configured
for this application, so a push to `handbook/` doesn't trigger a rebuild by itself — publishing
a handbook change still needs a manual **Deploy** click in Coolify's UI (see
**Operations → Maintaining the handbook**).
