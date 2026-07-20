# Operations: Restoring Forgejo from backup

> **Status: theoretical.** This procedure has not been tested end-to-end. It's built from
> Forgejo's official dump/restore documentation plus this fleet's actual container layout,
> but a real restore always surfaces gaps a plan can't. Whoever runs it for real should
> update this page with what actually happened (see Step 5).

## When you need this

Forgejo's data is lost, corrupted, or `forgejo-prod-01` has died. You have a backup archive
in Garage bucket `forgejo-backup` (7-day rolling retention) and need to restore Forgejo to
working state.

## What's in the backup

A daily systemd timer on `forgejo-prod-01` (22:59 UTC) runs `gitea dump --type zip --skip-log`
inside the `forgejo` container and uploads the result to Garage via rclone. Each archive is a
self-contained `gitea dump` zip containing:

- `app.ini` — Forgejo's resolved configuration
- `data/` — the contents of `/data/gitea` inside the container: avatars, attachments,
  packages, actions artifacts, and (for SQLite instances like this one) the database file
  itself
- `repos/` — the bare git repositories from `/data/git/repositories`
- a database dump file, for non-SQLite backends

This fleet's Forgejo runs SQLite (`FORGEJO__database__DB_TYPE=sqlite3`), so the database is
most likely included as the raw `.db` file inside `data/`, not a SQL text export — verify
this against the actual archive contents at restore time (`unzip -l`) before assuming either
shape.

## Prerequisites for restore

- A Docker host to run Forgejo (`forgejo-prod-01` rebuilt, or any other host)
- Network access to Garage (`192.168.50.80:3900`, bucket `forgejo-backup`)
- The fleet's age private key, for SOPS decryption of Garage credentials
- `sops` and `rclone` binaries (see Sprint 3v's host-prep — both were installed directly on
  `forgejo-prod-01` as standalone binaries, a new pattern for this fleet since SOPS
  previously only ran inside the custom Komodo Periphery image; see ADR-0005)

## Procedure

### Step 1 — Retrieve the backup

List available archives and download the one you want (most recent, unless you're recovering
from a specific point in time):

```bash
sops exec-env /opt/homelab/forgejo-backup/secrets.enc.env bash -c '
  RCLONE_CONFIG_GARAGE_TYPE=s3 \
  RCLONE_CONFIG_GARAGE_PROVIDER=Other \
  RCLONE_CONFIG_GARAGE_REGION=garage \
  RCLONE_CONFIG_GARAGE_ENDPOINT="$GARAGE_ENDPOINT" \
  RCLONE_CONFIG_GARAGE_ACCESS_KEY_ID="$GARAGE_ACCESS_KEY_ID" \
  RCLONE_CONFIG_GARAGE_SECRET_ACCESS_KEY="$GARAGE_SECRET_ACCESS_KEY" \
  RCLONE_CONFIG_GARAGE_FORCE_PATH_STYLE=true \
  rclone lsl garage:forgejo-backup/
'
```

Then copy the chosen archive down with `rclone copy garage:forgejo-backup/<name>.zip .`
(same env vars). If restoring on a fresh host that doesn't have `/opt/homelab/forgejo-backup/secrets.enc.env`
yet, decrypt Garage credentials from the repo's copy and the age key instead — the credentials
file itself is host-side only (see Sprint 3v's status report), not tracked in git.

### Step 2 — Prepare the restore target

If Forgejo's container and volume are gone, recreate them from `stacks/forgejo/compose.yml`
(`docker compose up -d` — this creates the `forgejo-data` volume but leaves it empty; that's
fine, the restore populates it). Stop the container before touching its data:

```bash
docker compose -f /opt/homelab/forgejo/compose.yml stop forgejo
```

### Step 3 — Restore the archive

Unzip the archive on the host, then copy pieces into the (stopped) container's volume. Exact
commands are version-specific — verify against `forgejo dump --help` and the archive's actual
layout (`unzip -l <archive>.zip`) before running any of this for real:

```bash
unzip forgejo-<timestamp>.zip -d /tmp/forgejo-restore
cd /tmp/forgejo-restore

# Copy into the running (stopped) container's volume mount point.
# Adjust paths if the volume's host-side mount differs from what
# `docker volume inspect forgejo-data` reports.
docker cp app.ini forgejo:/data/gitea/conf/app.ini
docker cp data/. forgejo:/data/gitea/
docker cp repos/. forgejo:/data/git/repositories/

# If the SQLite db came as a raw file inside data/, it's already
# in place from the data/ copy above. If instead a gitea-db.sql
# text dump is present, import it:
# docker exec forgejo sqlite3 /data/gitea/gitea.db < gitea-db.sql

docker exec forgejo chown -R git:git /data
```

### Step 4 — Verify

```bash
docker compose -f /opt/homelab/forgejo/compose.yml start forgejo
docker exec forgejo gitea admin regenerate hooks
```

Then check:
- Users can log in at `forgejo.ts.kazuki.uk`
- Repositories are present and their commit history is intact
- Forgejo Actions / the runner still connects (`forgejo-runner` container logs)
- The Komodo deploy-trigger webhook still fires (see
  [Deploy triggers](deploy-triggers.md)) — if the restore landed on a different host or the
  URL changed, the webhook needs re-registration in Forgejo's settings

### Step 5 — Update this runbook

If you're reading this because you just ran a real restore: update this page with what
actually happened — which steps were accurate, which weren't, what the archive's real
internal layout turned out to be, and how long it took. Remove the "theoretical" status once
a real restore has succeeded.

## Known unknowns

- Restore has not been tested. Steps 3–4 in particular may need adjustment once run for real.
- Whether the SQLite database ships as a raw `.db` file or a SQL text dump inside the archive
  is inferred, not verified — check `unzip -l` on a real archive before trusting either path.
- If restoring to a different host than the original, DNS (`forgejo.ts.kazuki.uk`) and the
  Komodo deploy-trigger webhook may need updates.
- `gitea admin regenerate hooks` syntax should be re-verified against the running Forgejo
  version at restore time (`docker exec forgejo gitea admin --help`).
