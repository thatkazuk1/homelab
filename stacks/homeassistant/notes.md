- Real hardware coupling preserved unchanged through adoption: `privileged: true`,
  `/dev/bus/usb` and `/dev/vhci` device passthrough, `/run/dbus` — for a USB Zigbee/Z-Wave
  dongle and Bluetooth.
- First adopted stack to skip SOPS entirely on a true no-secrets basis rather than
  file-based-secrets — the only env var is `TZ`. Home Assistant's own `secrets.yaml` lives
  inside the bind-mounted `config/` dir, which never enters the repo.
- The pre-adoption backup required `sudo tar` — some `.storage` files are root-owned `0600`
  on the host since HA runs as root inside the container. A first attempt failed mid-tar with
  permission errors and was discarded (truncated archive); the sudo retry produced a
  complete, verified 895K tarball (37 entries incl. the SQLite DB).
- **Known issue, not fixed:** `https://ha.ts.kazuki.uk/` resolves and Traefik terminates a
  valid cert, but HA's own `aiohttp` server rejects the request with `400: Bad Request`
  ("A request from a reverse proxy was received... but your HTTP integration is not set-up
  for reverse proxies"). Root cause is `configuration.yaml`'s `http.trusted_proxies` not
  being reconfigured after the fresh-install rebuild during standardisation — out of scope
  for the adoption sprint, logged as a carryover. Direct access (`192.168.50.3:8123`) works
  correctly.
