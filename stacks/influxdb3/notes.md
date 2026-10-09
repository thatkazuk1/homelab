- One secret in git: `secrets.enc.env` holds Explorer's `SESSION_SECRET_KEY`. Without a
  fixed key, Explorer makes a new key at each start, every session becomes a new anonymous
  user, and dashboards (which belong to that user) disappear after a restart. Dashboards
  belong to one browser session, so other browsers do not see them.
- The admin API token (`DEFAULT_API_TOKEN`) lives in a bind-mounted
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
- `explorer-dashboards.js` makes the "Speedtest" and "AdGuard DNS" dashboards. Dashboards
  belong to the browser session, so run it in the browser that you use for Explorer: open
  Explorer, open the browser console, paste the file, press Enter. It replaces dashboards
  with the same titles. Do not use Explorer's import for these: the import accepts only
  `timeseries`, `gauge`, `stat` and `table` panels, and Explorer's own export changes every
  chart to `timeseries`.
- Dashboard queries must be one flat `SELECT` whose first `WHERE` starts with
  `time >= now() - interval '...'`. Explorer replaces that clause with the range from the
  time picker, and puts its own range after the first `WHERE` in the query.
