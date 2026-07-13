- Every service carries `komodo.skip` — this compose file documents the running config but
  isn't the deployment source of truth. The host still runs its own plaintext `compose.env`
  at deploy time; no `sops exec-env` wrapper is actually invoked here (bootstrap circularity:
  Komodo can't manage the compose that runs Komodo). The `secrets.enc.env` committed
  alongside it is for documentation purposes only, inert at deploy time.
