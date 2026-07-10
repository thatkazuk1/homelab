# Stacks

Every Docker Compose stack running under Komodo management, one page each.
The list mirrors what's currently reconciled from the [`stacks/`](https://github.com/meetKazuki/homelab/tree/master/stacks)
directory of this repo.

Each page follows the same reference-card shape: what the stack does, where
it runs, how its secrets are handled, notable operational quirks, and
relevant architectural decisions.

Not every service on the fleet is here yet, and not everything under
`stacks/` gets its own catalog page. Notably absent:

- **Home Assistant** (on `core-01`) — manually managed, deliberately outside GitOps
- **`nas-01` media stack** (Jellyfin, arr-stack, qBittorrent+Gluetun, etc.) — deferred to its own careful adoption thread
- **Forgejo, Forgejo runner** — meta-infrastructure that hosts the pipeline itself; tracked at `stacks/forgejo/` and `stacks/forgejo-runner/` for the wiki goal, but deliberately not Komodo-managed (bootstrapping circularity — the tool that would manage them runs on infrastructure they provide)
- **Komodo Core** — the reconciler itself; not tracked under `stacks/` at all (nothing to adopt it into), same bootstrapping reasoning as above
- **`komodo-periphery`** — the per-host agent that makes every other page on this list possible; tracked at `stacks/komodo-periphery/` (plus a `nas-01`-specific variant) but it's fleet plumbing, not a catalog entry
- **`handbook`** — this site's own stack, tracked at `stacks/handbook/`; left off its own catalog for the obvious reason
- **Coolify and its tenants** — see [ADR notes on Coolify](../decisions/index.md) for why
