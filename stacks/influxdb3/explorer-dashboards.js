// Paste in the browser console on the InfluxDB 3 Explorer page.
// It makes (or remakes) the Speedtest and AdGuard DNS dashboards in this browser's session.
(async () => {
  const DASHBOARDS = [
  {
    "title": "Speedtest",
    "description": "Internet speed from speedtest-tracker (every 30 minutes).",
    "cells": [
      {
        "name": "Download now (Mbps)",
        "database": "speedtest-tracker",
        "viz": "single-stat",
        "x": 0,
        "y": 0,
        "w": 3,
        "h": 2,
        "query": "SELECT round(download_bits / 1e6, 1) AS download_mbps FROM speedtest WHERE time >= now() - interval '7 days' ORDER BY time DESC LIMIT 1"
      },
      {
        "name": "Upload now (Mbps)",
        "database": "speedtest-tracker",
        "viz": "single-stat",
        "x": 3,
        "y": 0,
        "w": 3,
        "h": 2,
        "query": "SELECT round(upload_bits / 1e6, 1) AS upload_mbps FROM speedtest WHERE time >= now() - interval '7 days' ORDER BY time DESC LIMIT 1"
      },
      {
        "name": "Ping now (ms)",
        "database": "speedtest-tracker",
        "viz": "single-stat",
        "x": 6,
        "y": 0,
        "w": 3,
        "h": 2,
        "query": "SELECT round(ping, 1) AS ping_ms FROM speedtest WHERE time >= now() - interval '7 days' ORDER BY time DESC LIMIT 1"
      },
      {
        "name": "Tests in range",
        "database": "speedtest-tracker",
        "viz": "single-stat",
        "x": 9,
        "y": 0,
        "w": 3,
        "h": 2,
        "query": "SELECT count(*) AS tests FROM speedtest WHERE time >= now() - interval '7 days'"
      },
      {
        "name": "Download and upload (Mbps)",
        "database": "speedtest-tracker",
        "viz": "line",
        "x": 0,
        "y": 2,
        "w": 12,
        "h": 4,
        "query": "SELECT time, round(download_bits / 1e6, 1) AS download_mbps, round(upload_bits / 1e6, 1) AS upload_mbps FROM speedtest WHERE time >= now() - interval '7 days' ORDER BY time"
      },
      {
        "name": "Latency: idle and under load (ms)",
        "database": "speedtest-tracker",
        "viz": "line",
        "x": 0,
        "y": 6,
        "w": 8,
        "h": 4,
        "query": "SELECT time, round(ping, 1) AS idle_ping, round(download_latency_avg, 1) AS loaded_download, round(upload_latency_avg, 1) AS loaded_upload FROM speedtest WHERE time >= now() - interval '7 days' ORDER BY time"
      },
      {
        "name": "Jitter and packet loss",
        "database": "speedtest-tracker",
        "viz": "line",
        "x": 8,
        "y": 6,
        "w": 4,
        "h": 4,
        "query": "SELECT time, round(ping_jitter, 1) AS jitter_ms, round(packet_loss, 2) AS packet_loss_pct FROM speedtest WHERE time >= now() - interval '7 days' ORDER BY time"
      },
      {
        "name": "Daily download spread (Mbps)",
        "database": "speedtest-tracker",
        "viz": "line",
        "x": 0,
        "y": 10,
        "w": 6,
        "h": 5,
        "query": "SELECT date_bin(interval '1 day', time) AS time, round(approx_percentile_cont(download_bits, 0.05) / 1e6, 1) AS p5, round(approx_percentile_cont(download_bits, 0.5) / 1e6, 1) AS median, round(approx_percentile_cont(download_bits, 0.95) / 1e6, 1) AS p95 FROM speedtest WHERE time >= now() - interval '7 days' GROUP BY 1 ORDER BY 1"
      },
      {
        "name": "Slowest hours of day: Mbps below the best hour (Lagos)",
        "database": "speedtest-tracker",
        "viz": "ranking",
        "x": 6,
        "y": 10,
        "w": 6,
        "h": 5,
        "query": "SELECT lpad(CAST(CAST(date_part('hour', time AT TIME ZONE 'Africa/Lagos') AS INT) AS VARCHAR), 2, '0') || ':00' AS hour, round((max(avg(download_bits)) OVER () - avg(download_bits)) / 1e6, 1) AS mbps_below_best FROM speedtest WHERE time >= now() - interval '7 days' GROUP BY 1 ORDER BY 2 DESC LIMIT 10"
      },
      {
        "name": "Recent tests",
        "database": "speedtest-tracker",
        "viz": "table",
        "x": 0,
        "y": 15,
        "w": 12,
        "h": 5,
        "query": "SELECT time, server_name, server_location, isp, round(download_bits / 1e6, 1) AS download_mbps, round(upload_bits / 1e6, 1) AS upload_mbps, round(ping, 1) AS ping_ms, packet_loss FROM speedtest WHERE time >= now() - interval '7 days' ORDER BY time DESC LIMIT 50"
      }
    ]
  },
  {
    "title": "AdGuard DNS",
    "description": "Hourly AdGuard query summaries from telegraf-adguard.",
    "cells": [
      {
        "name": "Queries",
        "database": "adguard-dns",
        "viz": "single-stat",
        "x": 0,
        "y": 0,
        "w": 3,
        "h": 2,
        "query": "SELECT sum(elapsed_ms_count) AS queries FROM dns_queries WHERE time >= now() - interval '1 day'"
      },
      {
        "name": "Blocked (%)",
        "database": "adguard-dns",
        "viz": "single-stat",
        "x": 3,
        "y": 0,
        "w": 3,
        "h": 2,
        "query": "SELECT round(100.0 * sum(CASE WHEN reason = 'blocklist' THEN elapsed_ms_count ELSE 0 END) / sum(elapsed_ms_count), 1) AS blocked_pct FROM dns_queries WHERE time >= now() - interval '1 day'"
      },
      {
        "name": "Cache hits (%)",
        "database": "adguard-dns",
        "viz": "single-stat",
        "x": 6,
        "y": 0,
        "w": 3,
        "h": 2,
        "query": "SELECT round(100.0 * sum(cached_sum) / sum(elapsed_ms_count), 1) AS cached_pct FROM dns_queries WHERE time >= now() - interval '1 day'"
      },
      {
        "name": "Answer time via upstream, incl. cache (ms)",
        "database": "adguard-dns",
        "viz": "single-stat",
        "x": 9,
        "y": 0,
        "w": 3,
        "h": 2,
        "query": "SELECT round(sum(elapsed_ms_mean * elapsed_ms_count) / sum(elapsed_ms_count), 1) AS upstream_ms FROM dns_queries WHERE time >= now() - interval '1 day' AND upstream <> 'none'"
      },
      {
        "name": "Queries per hour by result",
        "database": "adguard-dns",
        "viz": "area",
        "x": 0,
        "y": 2,
        "w": 12,
        "h": 4,
        "query": "SELECT time, sum(elapsed_ms_count) AS queries, reason FROM dns_queries WHERE time >= now() - interval '1 day' GROUP BY time, reason ORDER BY time"
      },
      {
        "name": "Top clients",
        "database": "adguard-dns",
        "viz": "ranking",
        "x": 0,
        "y": 6,
        "w": 4,
        "h": 5,
        "query": "SELECT client, sum(elapsed_ms_count) AS queries FROM dns_queries WHERE time >= now() - interval '1 day' GROUP BY client ORDER BY queries DESC LIMIT 15"
      },
      {
        "name": "Top clients: blocked",
        "database": "adguard-dns",
        "viz": "ranking",
        "x": 4,
        "y": 6,
        "w": 4,
        "h": 5,
        "query": "SELECT client, sum(elapsed_ms_count) AS blocked FROM dns_queries WHERE time >= now() - interval '1 day' AND reason = 'blocklist' GROUP BY client ORDER BY blocked DESC LIMIT 15"
      },
      {
        "name": "Top clients: rewrite",
        "database": "adguard-dns",
        "viz": "ranking",
        "x": 8,
        "y": 6,
        "w": 4,
        "h": 5,
        "query": "SELECT client, sum(elapsed_ms_count) AS rewritten FROM dns_queries WHERE time >= now() - interval '1 day' AND reason = 'rewrite' GROUP BY client ORDER BY rewritten DESC LIMIT 15"
      },
      {
        "name": "Upstream split",
        "database": "adguard-dns",
        "viz": "pie",
        "x": 0,
        "y": 11,
        "w": 4,
        "h": 4,
        "query": "SELECT upstream, sum(elapsed_ms_count) AS queries FROM dns_queries WHERE time >= now() - interval '1 day' AND upstream <> 'none' GROUP BY upstream ORDER BY queries DESC"
      },
      {
        "name": "Answer time per upstream, incl. cache (ms)",
        "database": "adguard-dns",
        "viz": "line",
        "x": 4,
        "y": 11,
        "w": 8,
        "h": 4,
        "query": "SELECT time, round(sum(elapsed_ms_mean * elapsed_ms_count) / sum(elapsed_ms_count), 1) AS mean_ms, upstream FROM dns_queries WHERE time >= now() - interval '1 day' AND upstream <> 'none' GROUP BY time, upstream ORDER BY time"
      },
      {
        "name": "Query types",
        "database": "adguard-dns",
        "viz": "pie",
        "x": 0,
        "y": 15,
        "w": 4,
        "h": 4,
        "query": "SELECT qtype, sum(elapsed_ms_count) AS queries FROM dns_queries WHERE time >= now() - interval '1 day' GROUP BY qtype ORDER BY queries DESC"
      },
      {
        "name": "Slowest answer per hour (ms)",
        "database": "adguard-dns",
        "viz": "line",
        "x": 4,
        "y": 15,
        "w": 8,
        "h": 4,
        "query": "SELECT time, max(elapsed_ms_max) AS max_ms FROM dns_queries WHERE time >= now() - interval '1 day' GROUP BY time ORDER BY time"
      }
    ]
  }
];
  const api = async (method, path, body) => {
    const r = await fetch('/api/influxdb' + path, {method, headers: {'Content-Type': 'application/json'},
      body: body === undefined ? undefined : JSON.stringify(body)});
    if (!r.ok) throw new Error(method + ' ' + path + ': ' + r.status + ' ' + await r.text());
    const t = await r.text(); return t ? JSON.parse(t) : null;
  };
  const existing = await api('GET', '/dashboards');
  for (const d of DASHBOARDS) {
    for (const e of existing.filter(e => e.title === d.title)) await api('DELETE', '/dashboards/' + e.id);
    const dash = await api('POST', '/dashboards', {title: d.title, description: d.description});
    const pos = {};
    for (const c of d.cells) {
      const cell = await api('POST', '/dashboards/' + dash.id + '/cell', {name: c.name, database: c.database,
        query: c.query, queryLanguage: 'sql', visualizationType: c.viz});
      pos[cell.id] = c;
    }
    const layouts = await api('GET', '/dashboards/' + dash.id + '/layout');
    await api('PUT', '/dashboards/' + dash.id + '/layout/bulk', layouts.map(l => {
      const c = pos[l.cell.id];
      return {id: l.id, i: l.i, x: c.x, y: c.y, w: c.w, h: c.h, dashboardId: dash.id};
    }));
    console.log('Made dashboard', d.title, 'with', d.cells.length, 'cells:', location.origin + '/dashboards/' + dash.id);
  }
})();
