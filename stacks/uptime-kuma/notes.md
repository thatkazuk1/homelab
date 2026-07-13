- The named volume `uptime-kuma-data` is declared `external: true` — deliberately, not by
  oversight. It was live-migrated during adoption from Docker's original auto-derived name
  (`uptime-kuma_uptime-kuma-data`) to the clean explicit name, verified byte-identical before
  cutover, and marked external so Compose doesn't try to (re)create it.
- The fleet's first from-scratch Komodo adoption (Sprint 3b.1) — `uptime-kuma` was originally
  planned as the very first proof-of-loop stack (per ADR-0002) for exactly this reason: low
  risk, immediately visible if something breaks, and a chance to confirm Periphery runs
  cleanly on `core-01`'s ARM architecture early.
- A personal `Makefile` (`make up`/`down`) once sat alongside the compose file — a real risk,
  since an accidental `make up` could have silently reattached the old, un-migrated volume.
  Retired rather than reconciled.
