# Komodo Core — Database Restore Runbook

**Last updated:** 2026-06-30
**Applies to:** `komodo-prod-01` (192.168.50.111)

## Backup location

`/opt/homelab/komodo/backups/`

Each run produces:
- A timestamped folder (`YYYY-MM-DD_HH-MM-SS/`) containing per-collection `.gz` files
- A `Stats.gz` at the top level (excluded from restore by default)

Backup files are owned `root:root` — all restore commands below require `sudo`.

## Restore procedure

> **Warning:** If the target database is already populated, old documents will remain
> alongside restored ones. Drop the target database before restoring to a clean state.

```bash
sudo docker run --rm \
  -v /opt/homelab/komodo/backups:/backups \
  -e KOMODO_CLI_DATABASE_TARGET_ADDRESS=ferretdb:27017 \
  -e KOMODO_CLI_DATABASE_TARGET_USERNAME=<KOMODO_DATABASE_USERNAME from compose.env> \
  -e KOMODO_CLI_DATABASE_TARGET_PASSWORD=<KOMODO_DATABASE_PASSWORD from compose.env> \
  -e KOMODO_CLI_DATABASE_TARGET_DB_NAME=komodo-restore \
  --network komodo_default \
  ghcr.io/moghtech/komodo-cli \
  km database restore -y --restore-folder <TIMESTAMP>
```

Replace `<TIMESTAMP>` with the folder name, e.g. `2026-06-30_00-45-59`.

## Schedule

Daily at `01:00 UTC` (02:00 Africa/Lagos) via the `Backup Core Database` procedure in Komodo UI.
Komodo Core has no `TZ` set — all times are UTC.

## Offsite copy

Deferred to Sprint 3+ (rsync/restic to Garage S3).
