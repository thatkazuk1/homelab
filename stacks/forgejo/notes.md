- The Forgejo Actions runner registers against this instance via the modern
  `server.connections` config-file mechanism — Forgejo 15's `register` CLI subcommand is
  deprecated and no longer works against this instance's registration-token API.
- The tracked compose drifted once from the live host (missing
  `FORGEJO__webhook__ALLOWED_HOST_LIST`), caught and synced during Sprint 3i's meta-infra
  audit.

## Backup and restore

Forgejo's daily backup runs via a systemd timer on `forgejo-prod-01`
(not Komodo, not the stack itself). Backup archives land in Garage
bucket `forgejo-backup`, 7-day rolling retention.

Restore procedure documented at [Restoring Forgejo](../operations/restoring-forgejo.md).
