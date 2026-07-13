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
