# Stacks

Every Docker Compose stack running under Komodo management, one page each.
The list mirrors what's currently reconciled from the [`stacks/`](https://github.com/meetKazuki/homelab/tree/master/stacks)
directory of this repo.

Each page follows the same reference-card shape: what the stack does, where
it runs, how its secrets are handled, notable operational quirks, and
relevant architectural decisions.

Not every service on the fleet is here yet, and not everything under
`stacks/` gets its own catalog page. As of Sprint 3o, pages are auto-generated from each
stack's `stacks/<name>/compose.yml` — meta-infrastructure stacks with a single compose file
(Komodo Core, Forgejo, the Forgejo Actions runner) now get a page like any other, marked
`meta-infra` in their reference table. Notably still absent:

- **`nas-01` media stack** (Jellyfin, arr-stack, qBittorrent+Gluetun, etc.) — deferred to its own careful adoption thread
- **`komodo-periphery`** — the per-host agent that makes every other page on this list possible; tracked at `stacks/komodo-periphery/` as one `compose.<host>.yml` file per host (config genuinely diverges per host), which the generator doesn't yet handle — see `handbook/docs/operations/maintaining-handbook.md`
- **Coolify and its tenants** — deliberately outside Komodo/git management, no single `compose.yml` to generate from; see [Architecture → Coolify](../architecture/coolify.md)
