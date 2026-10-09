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
- `SECRET_KEY` and `LIVE_SERVER_SECRET_KEY` held Plane's public installer defaults until
  2026-10-08. On that date, both keys and the Postgres, RabbitMQ and MinIO credentials got
  new random values in `secrets.enc.env`. The compose fallback defaults still exist, but the
  secrets file overrides them. The new database credentials needed empty volumes, so the
  stack was rebuilt from nothing, and the old Plane data is gone.
- When a Komodo deploy does not create the containers (the `deploy.replicas` parser WARN,
  see Deploy triggers), deploy from inside Periphery on `plane-prod-01`:
  `docker exec -w /etc/komodo/stacks/plane/stacks/plane komodo-periphery sops exec-env secrets.enc.env 'docker compose -p plane-app up -d'`.
  The checkout is inside the Periphery container, not on the host filesystem. After a fresh
  start, the API waits until all database migrations finish. The web UI shows "Plane didn't
  start up correctly" for about two minutes.
- `plane.kazuki.uk` is behind Cloudflare Access (2026-10-09), so a public request gets the
  Access login page first. On the LAN, AdGuard resolves the name to Traefik directly, so LAN
  requests do not go through Access.
- Adopted with its vendor-supplied multi-service topology intact, per the "don't reorganize a
  working topology mid-migration" discipline.
