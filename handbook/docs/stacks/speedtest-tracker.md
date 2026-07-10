# speedtest-tracker

Scheduled internet speed tests with historical tracking.

**Host:** `telemetry-prod-01`
**Access:** ports `8080`/`8443` on the host; the actual `APP_URL` is configured via a secret
var, not reproduced here
**Repo:** [`stacks/speedtest-tracker/`](https://github.com/meetKazuki/homelab/tree/master/stacks/speedtest-tracker)

## What it does

A LinuxServer.io-packaged Laravel app (`lscr.io/linuxserver/speedtest-tracker`) that runs
internet speed tests on a schedule and keeps a queryable history, with an optional public
dashboard view. It shares `telemetry-prod-01` with [`influxdb3`](influxdb3.md) as a separate
compose project, not a bundled one.

## Configuration

- **Compose:** single-service. Kept the pre-adoption `${VAR}` interpolation style in the
  `environment:` block rather than rewriting to bare pass-through, matching the precedent set
  by [`sure`](sure.md).
- **Secrets:** full ADR-0010 pattern — `secrets.enc.env` carries a real Laravel `APP_KEY`
  plus `PUID`, `PGID`, `TZ`, `APP_URL`, `ASSET_URL`, `SPEEDTEST_SCHEDULE`.
- **Data:** bind mount, `/opt/homelab/speedtest-tracker/config:/config` — includes a SQLite
  database that also holds this app's InfluxDB write-token integration as app-managed state,
  the same pattern [`beszel`](beszel.md) uses for its S3 config (not an env var).

## Notable

- A real behavioral regression was caught during adoption's resolved-config diff: the
  original `env_file:` implicitly passed a bare `TZ` value into the container (the LSIO base
  image reads system `TZ` separately from the app's own `DISPLAY_TIMEZONE` setting) — the
  first conversion draft dropped it, restored as an explicit `TZ=${TZ}` pass-through
  alongside `DISPLAY_TIMEZONE`.
- This is the reference case in `docs/project-state.md`'s "Known odd behaviors" for a pair of
  unresolved, Komodo-side transient faults: one deploy where every `${VAR}` substitution came
  through blank despite a correctly-configured wrapper, and a separate silent
  webhook-dispatch stall. Both were resolved by operator-side UI changes, neither
  conclusively root-caused. Worth checking this page's cross-reference if a similar symptom
  shows up on another stack.

## See also

- [`influxdb3`](influxdb3.md) — the other stack on this host
- [`beszel`](beszel.md) — shares the app-managed-config-over-env-var pattern for its own
  integration secret
