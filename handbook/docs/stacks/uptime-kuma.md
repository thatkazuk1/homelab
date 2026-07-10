# uptime-kuma

Uptime and status monitoring for the fleet — the dashboard that shows what's up, what's
down, and for how long.

**Host:** `core-01`
**Access:** host networking on `core-01` (192.168.50.3), default Uptime Kuma port
**Repo:** [`stacks/uptime-kuma/`](https://github.com/meetKazuki/homelab/tree/master/stacks/uptime-kuma)

## What it does

A self-hosted status page and monitor runner: HTTP/TCP/ping checks against services across
the fleet, with historical uptime data and alerting. It's the fleet's reference case for
"is anything actually broken right now," and the thing other stacks' redeploys are cross-checked
against (e.g. confirming a container reappears healthy after a Komodo-triggered recreation).

## Configuration

- **Compose:** single-service, `louislam/uptime-kuma:2`, `network_mode: host`
- **Secrets:** none. `PUID`/`PGID`/`TZ` are the only env vars, inlined as literals — this is
  the fleet's no-secrets reference stack (no `secrets.enc.env`, no wrapper)
- **Data:** one named volume, `uptime-kuma-data`, declared `external: true` — deliberately,
  not by oversight. It was live-migrated during adoption from Docker's original auto-derived
  name (`uptime-kuma_uptime-kuma-data`) to the clean explicit name, verified byte-identical
  before cutover, and marked external so Compose doesn't try to (re)create it.

## Notable

- The fleet's first from-scratch Komodo adoption (Sprint 3b.1) — `uptime-kuma` was originally
  planned as the very first proof-of-loop stack (per ADR-0002) for exactly this reason: low
  risk, immediately visible if something breaks, and a chance to confirm Periphery runs
  cleanly on `core-01`'s ARM architecture early.
- A personal `Makefile` (`make up`/`down`) once sat alongside the compose file — a real risk,
  since an accidental `make up` could have silently reattached the old, un-migrated volume.
  Retired rather than reconciled.

## See also

- [Adopting a stack](../operations/adopting-a-stack.md)
- [ADR-0002 Komodo for Docker GitOps](../decisions/0002-komodo-for-docker-gitops.md)
