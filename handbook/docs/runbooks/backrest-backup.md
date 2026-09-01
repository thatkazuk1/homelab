# Backrest Backup

## Overview

Backrest runs as a Komodo-managed stack on `docker-prod-01`
(`stacks/backrest/compose.yml`), providing a restic-based backup of that
host's own stack data. UI at `https://backrest.ts.kazuki.uk`.

**What's backed up (single plan, `docker-prod-01`):**

| Source | Path in container | Notes |
|---|---|---|
| Vaultwarden | `/sources/vaultwarden/data` | Vault DB + attachments |
| Homepage | `/sources/homepage/config`, `/sources/homepage/assets` | Dashboard config, custom icons/images |
| Cloudflared | `/sources/cloudflared/config` | Tunnel config |
| Sure Finance | `/sources/sure/app-storage`, `/sources/sure/postgres-data` | App storage (Docker volume `sure_app-storage`) + Postgres data dir (Docker volume `sure_postgres-data`), both mounted read-only by volume name |
| Beszel | `/sources/beszel/beszel-data` | Hub config + monitoring history (Docker volume `beszel_beszel-data`) |

All source mounts are read-only and were verified against each stack's
**actually running container** (`docker inspect <container> --format
'{{range .Mounts}}...'`), not assumed from the compose file — Sure and
Beszel use Docker named volumes rather than bind mounts, which need
external volume references (`external: true` + `name:`) in
`stacks/backrest/compose.yml` rather than plain host paths.

**Known caveat:** Sure's Postgres data directory is backed up as a live
file-level copy while Postgres is running, not via `pg_dump`. This is not
guaranteed to be a transactionally consistent snapshot the way a logical
dump would be — Postgres's own crash recovery makes a restore *likely*
to work, but this hasn't been tested. If Sure's data ever needs to be
treated as more critical than "best effort," add a `pg_dump`-based
pre-backup hook instead of relying on the raw file copy.

**Not backed up (this stack; excluded deliberately):**
- `sure_redis-data` — cache/session store, not durable data
- `beszel_beszel-socket` — a Unix socket, not data
- Compose files (Forgejo-tracked already)
- Media library files, Docker images, InfluxDB raw metrics (per sprint scope)

## Destination

**Google Drive only**, via restic's `rclone:` backend. There is
deliberately **no local repo** — an earlier local repo
(`docker-prod-01-local`, `/opt/homelab/backrest-repos` on the host) was
created and verified working during setup, but the operator chose to
drop it in favor of a single Drive-only plan for simplicity. The local
repo's files still exist on disk at `/opt/homelab/backrest-repos` but are
no longer registered in Backrest and receive no new snapshots.

**This means the current setup does not meet a 3-2-1 backup posture** —
it's 2 copies (original + one offsite copy), one location type. See
`project-state.md`'s note on this gap. If `docker-prod-01` and Google
Drive were both unavailable, or if the Drive copy were corrupted, there
is no second independent copy.

- **Repo:** `gdrive-kukiito219` (name chosen by Backrest UI at repo
  creation; not the name originally planned)
- **Backend URI:** `rclone:gdrive:Backups/docker-prod-01-backrest-homelab/`
  (nested under an existing `Backups` folder in the Drive account,
  not a top-level `backrest-homelab` folder as originally planned — a
  same-named top-level folder was created earlier in setup and is now an
  unused, empty leftover)
- **rclone auth:** env-var driven (`RCLONE_CONFIG_GDRIVE_*`), no
  `rclone.conf` file. Values live in `stacks/backrest/secrets.enc.env`,
  decrypted at deploy time via the stack's `sops exec-env` Compose Cmd
  Wrapper, same as every other fleet stack's secrets.
- **Rate limiting:** `RCLONE_TPSLIMIT=8` to avoid Drive API throttling.

## Schedule and retention

- **Schedule:** daily at 23:59 (`59 23 * * *`, `CLOCK_LOCAL` — resolves
  to `Africa/Lagos`/WAT per the container's `TZ` setting)
- **Retention:** 7 daily, 4 weekly, 2 monthly (Backrest also keeps a
  24-hour hourly bucket by default; with only one run per day this bucket
  never holds more than one snapshot, so it's a no-op in practice)

## Checking backup status

UI: `https://backrest.ts.kazuki.uk`. The plan's run history shows
success/failure and duration per run.

From the shell, on `docker-prod-01`:
```bash
docker logs backrest --since 24h | grep -iE "docker-prod-01|error"
```

Config and snapshot metadata (not secret-bearing, but requires root —
Backrest's container runs as root and owns these files):
```bash
sudo python3 -c "
import json
c = json.load(open('/etc/komodo/repos/kazuki/homelab/stacks/backrest/config/config.json'))
for p in c['plans']:
    print(p['id'], p['repo'], p['schedule'], p['retention'])
"
```

## Restoring files (theoretical — not tested)

1. Open `https://backrest.ts.kazuki.uk`, select the `gdrive` repo.
2. Browse snapshots, pick the one to restore from.
3. Use Backrest's restore-to-path feature to restore into a scratch
   directory on `docker-prod-01` (not directly over the live path) —
   inspect before copying over the live data.
4. For Sure's Postgres path specifically: given the live-copy caveat
   above, verify the restored data directory starts cleanly under
   Postgres (check container logs for successful crash recovery) before
   trusting it — don't assume a clean restore without checking.

## Restoring if the local Backrest instance / `docker-prod-01` is lost

Since the local repo is gone, the Google Drive copy is the *only* copy.
Theoretical procedure:

1. Stand up a new Backrest instance (or restic CLI directly) anywhere
   with network access to Google Drive.
2. Reconstruct rclone's Google Drive remote from
   `stacks/backrest/secrets.enc.env` (`RCLONE_CONFIG_GDRIVE_*` vars —
   `sops -d stacks/backrest/secrets.enc.env`) plus the repo password
   (`BACKREST_LOCAL_REPO_PASSWORD` in the same file — note this var name
   is a leftover from when it was the local repo's password; it's now
   also the Google Drive repo's password, since the same value was
   reused rather than generating a second one).
3. Point restic at `rclone:gdrive:Backups/docker-prod-01-backrest-homelab/`
   with that password and restore.

This path has not been exercised. Treat it as a starting point, not a
verified runbook.

## Credential locations

- **Google OAuth Client ID/Secret + Drive refresh token:** SOPS-encrypted
  in `stacks/backrest/secrets.enc.env` (`RCLONE_CONFIG_GDRIVE_*`).
  Decrypted into the container at deploy time via the Komodo Stack's
  `sops exec-env secrets.enc.env '[[COMPOSE_COMMAND]]'` wrapper.
- **Restic repo password:** same file, `BACKREST_LOCAL_REPO_PASSWORD`.
  Not container-consumed — Backrest's repo password field has no
  documented env-var substitution, so it's entered directly in the UI.
  This SOPS entry is a disaster-recovery record only.
- **ntfy Shoutrrr URL (`svc-backrest` user, write-only to
  `homelab-backup-failures`):** same file,
  `BACKREST_NTFY_SHOUTRRR_URL`. Also UI-entered, not container-consumed —
  same record-only treatment.
- **Backrest's own admin login:** set via its first-run UI wizard, not
  stored anywhere in this repo (operator-held).

## Monitoring

A `Shoutrrr` hook on the `docker-prod-01` plan, condition
`CONDITION_ANY_ERROR`, posts to ntfy topic `homelab-backup-failures`
(same topic Forgejo's backup uses — see
`handbook/docs/operations/` for that setup) via a dedicated
`svc-backrest` ntfy user (write-only to that topic, per the
scoped-credential-per-consumer convention). Fires on failure of the
backup itself or of the prune/check/forget steps that run alongside it.
Silent on success — verified by a deliberate test (a throwaway plan with
a nonexistent source path) rather than assumed from the config.

## Troubleshooting

- **Container won't start / restarts:** `docker logs backrest`. Check
  the SOPS wrapper is actually set on the Komodo Stack (`sops exec-env
  secrets.enc.env '[[COMPOSE_COMMAND]]'`) — without it, the
  `RCLONE_CONFIG_GDRIVE_*` pass-through env vars in the compose file
  resolve empty and rclone will fail to authenticate.
- **rclone auth failures:** the Drive token can expire; rclone
  auto-refreshes using the stored `refresh_token` as long as the client
  ID/secret are still valid. If refresh itself fails (e.g. the OAuth
  consent was revoked in the Google account), a new token needs to be
  generated via `rclone authorize drive <client_id> <client_secret>`
  from a machine with a browser, then re-encrypted into
  `secrets.enc.env`.
- **A specific source path fails:** check the failing container is
  actually running and the mount still exists — `docker inspect
  backrest --format '{{range .Mounts}}{{.Source}} -> {{.Destination}}
  {{println}}{{end}}'`. A stack rename or volume rename on the source
  side will silently break that one path without affecting the others.
- **No ntfy notification on a real failure:** confirm the hook is still
  attached to the `docker-prod-01` plan (hooks are per-plan, not global —
  editing/recreating a plan does not carry hooks over automatically).

## Deferred / not in scope this sprint

- **Remote-host backup** (`proxy-prod-01`, `telemetry-prod-01`,
  `core-01`) — **blocked on an architecture gap discovered mid-sprint**:
  Backrest has no feature for backing up data on a different host. It
  only backs up local paths/Docker volumes on the machine it runs on;
  restic's `sftp:`/`rclone:` backends configure where the *repository* is
  stored, not where source data is read from. The originally-planned
  "restic over SSH on remote hosts" architecture does not correspond to
  any real Backrest capability. The likely path forward is SSHFS- or
  NFS-mounting the remote hosts' data directories onto `docker-prod-01`
  so Backrest can back them up as local paths — this is a real
  architecture decision (reliability of network-mount-based backup,
  mount lifecycle management) that needs the planner's input, not
  something to substitute in silently.
- `nas-01` — deferred, TOS Shared Folder limitation (per original sprint
  scope).
- 3-2-1 gap — see the Destination section above.
