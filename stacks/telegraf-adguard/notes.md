- Purpose: Telegraf reads the AdGuard Home query log on `core-01`. It writes one summary row each hour to InfluxDB 3 on `telemetry-prod-01`. The database is `adguard-dns` with a retention period of 365 days.
- AdGuard keeps its own statistics for a short time only. This stack keeps the long-term history.

## What the stack stores

- Measurement `dns_queries`. One row for each hour and each combination of the four tags.
- Tags: `client` (the client IP address), `reason`, `qtype`, `upstream`.
- `reason` is a name that Telegraf maps from the AdGuard reason code: `none`, `allowlist`, `error`, `blocklist`, `safebrowsing`, `parental`, `invalid`, `safesearch`, `blocked_service`, `rewrite`, `rewrite_hosts`, `rewrite_rule`. A code that is not known becomes `other`.
- `upstream` is `none` when AdGuard answers from the cache or answers itself (block, rewrite).
- Fields: `elapsed_ms_count` (number of queries), `elapsed_ms_mean`, `elapsed_ms_max` (milliseconds), and `cached_sum` (number of queries that the cache answered).
- The timestamp of a row is the end of the hour in UTC.

## What the stack does not store

- The domain name of a query (`QH`), the answers, the filter rules, and the time of a single query.
- The parser reads only the listed JSON paths (`T`, `IP`, `QT`, `Result.Reason`, `Upstream`, `Elapsed`, `Cached`). The domain key is not in the list, so the domain never enters a Telegraf metric or InfluxDB.
- The `client` tag is an IP address. This is personal data about the household. It stays for 365 days. To remove it, delete the `client` tag from the `[[inputs.tail.json_v2.tag]]` list and from the Starlark code, and delete the table.

## Privacy: one residual risk

- Telegraf writes a line to its error log when a log line is not valid JSON or has a wrong type. The error text contains the whole line, and the line contains the domain.
- AdGuard writes valid JSON, and the tail input waits for the end of a partial line (tested). The case is rare.
- The compose file limits the container log to 2 files of 1 MB, so such a line leaves the host quickly. Do not copy `docker logs` output into a ticket or a chat.
- To remove the risk fully, set `logging: driver: none`. Then a write failure to InfluxDB is not visible in the logs.

## Mount and access

- The stack mounts the folder `/opt/AdGuardHome/querylog` read-only, not the file `querylog.json`. AdGuard rotates the log by rename (`querylog.json` to `querylog.json.1`). A file mount would follow the old file. A folder mount follows the name.
- The operator moves the AdGuard query log to this folder. This stack does not change AdGuard.
- The log file is `root:root` with mode 0600. The container runs as root with `cap_drop: [ALL]`. The owner can read the file without a capability. The container has a read-only root file system. Only the state volume `telegraf-adguard-state` is writable.

## InfluxDB token

- InfluxDB 3 Core has admin tokens only. It has no token that can write to one database only.
- The writer token `telegraf-adguard` is therefore an admin token. A person who holds it can read, write and delete every database on `telemetry-prod-01`.
- Controls: the token is in `secrets.enc.env` (SOPS) only. The host firewall on `telemetry-prod-01` allows port 8181 from `192.168.50.3` (`core-01`) for this stack.
- Rotation: create a new token with `influxdb3 create token --admin --name <new-name>`, encrypt it into `secrets.enc.env`, deploy, and then delete the old token with `influxdb3 delete token --token-name telegraf-adguard`. Do not use `--regenerate`. That option replaces the operator token that Explorer uses.
- Run the `influxdb3` CLI with `docker exec -e INFLUXDB3_AUTH_TOKEN influxdb3-core influxdb3 ...`. Read the Explorer token from `/opt/homelab/influxdb3/config/config.json` into an exported variable. Never print it.

## Behavior to know

- The hourly window ends on the full hour (UTC). Telegraf holds the data of the current hour in memory.
- A normal stop (`docker stop`, a Komodo redeploy) writes the partial row at once. The row has the stop time as its timestamp, so the next row does not overwrite it (tested with a 60-second window).
- A crash or a power loss loses up to one hour of data.
- Telegraf saves the read offset in the state volume. A restart continues from the saved offset. A stop does not lose log lines.
- The saved offset belongs to a hash of the `[[inputs.tail]]` settings. After a change to those settings, the offset is lost. Telegraf then starts at the end of the log, and the lines written during the stop are lost.
- If AdGuard rotates the log while Telegraf is stopped, the saved offset can point into the new file. Expect a small loss of data in that case.
- The first deploy starts at the end of the log. Older log content is not imported.

## Query limit of InfluxDB 3 Core

- Core queries only the last 72 hours of data, and no more than 432 Parquet files (`INFLUXDB3_QUERY_FILE_LIMIT`).
- This stack writes at about 1 file each hour, so about 18 days (432 files) are queryable. Older rows stay on disk for the 365-day retention period but a query does not reach them.
- To query more history, raise `INFLUXDB3_QUERY_FILE_LIMIT` on the `influxdb3-core` service in `stacks/influxdb3/compose.yml`. A higher limit uses more memory for each query. This change is not part of this stack.

## Query in InfluxDB 3 Explorer

Open Explorer, choose the database `adguard-dns`, and use the SQL editor.

```sql
-- Queries each day, split by reason
SELECT date_bin(INTERVAL '1 day', time) AS day, reason, SUM(elapsed_ms_count) AS queries
FROM dns_queries
WHERE time >= now() - INTERVAL '14 days'
GROUP BY 1, 2 ORDER BY 1, 2;

-- Block rate and cache hit rate each day
SELECT date_bin(INTERVAL '1 day', time) AS day,
       SUM(CASE WHEN reason IN ('blocklist','blocked_service','safebrowsing','parental')
                THEN elapsed_ms_count ELSE 0 END) / SUM(elapsed_ms_count) AS block_rate,
       SUM(cached_sum) / SUM(elapsed_ms_count) AS cache_hit_rate
FROM dns_queries
WHERE time >= now() - INTERVAL '14 days'
GROUP BY 1 ORDER BY 1;

-- Top clients and mean answer time (weighted by the number of queries)
SELECT client, SUM(elapsed_ms_count) AS queries,
       SUM(elapsed_ms_mean * elapsed_ms_count) / SUM(elapsed_ms_count) AS mean_ms
FROM dns_queries
WHERE time >= now() - INTERVAL '7 days'
GROUP BY client ORDER BY queries DESC LIMIT 10;
```

- Use `SUM(elapsed_ms_count)` for a count. A row is a summary, so `COUNT(*)` counts rows, not queries.
- A mean of the `elapsed_ms_mean` column is not correct. Weight it with `elapsed_ms_count` as shown above.
