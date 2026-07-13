- The real deployment path (`/home/nexus-plane/plane/plane-app/`, compose project
  `plane-app`) diverged sharply from what was assumed going into its adoption — worth
  remembering that this repo's `stacks/plane/` directory name doesn't match the host's own
  directory structure, only Komodo's Run Directory/Project Name fields do.
- A live-but-inert secret was found during adoption: `POSTGRES_PASSWORD` didn't match what
  Postgres actually authenticated with, because the app's `DATABASE_URL` fell back to a
  hardcoded default in the vendor compose file rather than being built from the Postgres
  vars. Preserved byte-for-byte during adoption itself (never fix a landmine mid-migration),
  then fixed deliberately in a follow-up sprint once verified live against Postgres's actual
  running password.
- `SECRET_KEY` / `LIVE_SERVER_SECRET_KEY` were, as of the most recent check, still Plane's own
  public installer default values — never rotated since install. Independent of any
  transcript-exposure concern; the operator has elected to handle this at their own
  convenience.
- Adopted with its vendor-supplied multi-service topology intact, per the "don't reorganize a
  working topology mid-migration" discipline.
