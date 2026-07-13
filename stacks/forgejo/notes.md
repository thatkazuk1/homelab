- The Forgejo Actions runner registers against this instance via the modern
  `server.connections` config-file mechanism — Forgejo 15's `register` CLI subcommand is
  deprecated and no longer works against this instance's registration-token API.
- The tracked compose drifted once from the live host (missing
  `FORGEJO__webhook__ALLOWED_HOST_LIST`), caught and synced during Sprint 3i's meta-infra
  audit.
