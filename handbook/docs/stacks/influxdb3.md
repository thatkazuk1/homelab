# influxdb3

Time-series database (InfluxDB 3 Core + Explorer) backing the fleet's telemetry data, such as speedtest history.

## Reference

| Field | Value |
|---|---|
| Host | `telemetry-prod-01` |
| Category | monitoring |
| Status | adopted |
| Repo path | [`stacks/influxdb3/`](https://github.com/meetKazuki/homelab/tree/master/stacks/influxdb3) |

## Services

### `influxdb3-core`

- **Image:** `influxdb:3-core`
- **Container:** `influxdb3-core`
- **Restart policy:** `unless-stopped`
- **Ports:** `8181:8181`

### `influxdb3-explorer`

- **Image:** `influxdata/influxdb3-ui:1.8.0`
- **Container:** `influxdb3-explorer`
- **Restart policy:** `unless-stopped`
- **Ports:** `8888:8080`, `8889:8888`

## Secrets

No SOPS-encrypted secrets file. Configuration lives in the compose file directly or in bind-mounted files on the host.

## Operational notes

- No secrets in git. The admin API token (`DEFAULT_API_TOKEN`) lives in a bind-mounted
  `config/config.json` (Explorer's own config file), confirmed present by key name only,
  never printed.
- Plain bind-mounted directories under `/opt/homelab/influxdb3/` (`data`, `plugins`,
  `config`, `explorer-db`) — no named Docker volumes at all, simpler than most adopted
  stacks.
- Core enforces authentication on every endpoint, including `/ping` — a `401` there is
  correct strict-auth behavior, not a fault.
- Verification during adoption had to be routed through the host itself (`curl` run on
  `telemetry-prod-01`), since an executor session's own shell can't resolve internal
  hostnames or reach LAN-only ports directly.

---

*This page is auto-generated from `stacks/influxdb3/compose.yml`. Reference-level content (host, services, images, secrets pattern) reflects the compose file's current state. Manual edits to this page will be overwritten on next generation. To change reference content, edit the compose file. To add operational context, edit `stacks/influxdb3/notes.md`.*
