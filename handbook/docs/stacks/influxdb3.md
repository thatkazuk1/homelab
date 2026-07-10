# influxdb3

Time-series database backing the fleet's telemetry (speedtest history, and future metrics
sources).

**Host:** `telemetry-prod-01`
**Access:** Explorer admin UI on the host's bound ports (`8888`/`8889`); Core's own API on
`8181` — no public or `.lan` domain currently assigned, reached directly via host IP
**Repo:** [`stacks/influxdb3/`](https://github.com/meetKazuki/homelab/tree/master/stacks/influxdb3)

## What it does

InfluxDB 3 Core is the time-series database itself; InfluxDB 3 Explorer is its bundled admin
UI, running as a second container in the same compose project. Together they're
`telemetry-prod-01`'s data-storage half — [`speedtest-tracker`](speedtest-tracker.md) is the
other stack on this host, and a separate compose project entirely (the two were originally
assumed to possibly be one bundled stack; they're not).

## Configuration

- **Compose:** two services, `influxdb3-core` and `influxdb3-explorer` (depends on core)
- **Secrets:** none in git. The admin API token (`DEFAULT_API_TOKEN`) lives in a
  bind-mounted `config/config.json` (Explorer's own config file), confirmed present by key
  name only, never printed.
- **Data:** plain bind-mounted directories under `/opt/homelab/influxdb3/` (`data`, `plugins`,
  `config`, `explorer-db`) — no named Docker volumes at all, simpler than most adopted
  stacks.

## Notable

- Core enforces authentication on every endpoint, including `/ping` — a `401` there is
  correct strict-auth behavior, not a fault.
- Verification during adoption had to be routed through the host itself (`curl` run on
  `telemetry-prod-01`), since an executor session's own shell can't resolve internal
  hostnames or reach LAN-only ports directly.

## See also

- [`speedtest-tracker`](speedtest-tracker.md) — the other stack on this host
