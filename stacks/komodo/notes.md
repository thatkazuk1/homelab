- Every service carries `komodo.skip` — this compose file documents the running config but
  isn't the deployment source of truth. The host still runs its own plaintext `compose.env`
  at deploy time; no `sops exec-env` wrapper is actually invoked here (bootstrap circularity:
  Komodo can't manage the compose that runs Komodo). The `secrets.enc.env` committed
  alongside it is for documentation purposes only, inert at deploy time.
- The host file `/opt/homelab/komodo/compose.yml` differs from this file: its `core` and
  `periphery` services read `env_file: ./compose.env`. Start the host stack with
  `docker compose --env-file compose.env ...` (as the host `Makefile` does), so that
  interpolation is the same. `make up` uses `--force-recreate` and restarts Core too.
- Since 2026-10-09 the `periphery` service sets `PERIPHERY_DISABLE_TERMINALS` and
  `PERIPHERY_DISABLE_CONTAINER_EXEC` to `"true"`, in an `environment:` block in the host file and
  in this file. To change only the Periphery without touching Core, run
  `docker compose --env-file compose.env up -d --no-deps periphery` in `/opt/homelab/komodo`
  (use `--dry-run` first).
