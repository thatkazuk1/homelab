# Operations: nas-01 arr stack performance degradation

What to do when Sonarr/Radarr/Lidarr/Bazarr (or the wider arr stack on `nas-01`) become slow or
unreachable, without necessarily being crashed.

## The pattern

`qbittorrent`'s memory footprint grows over time — observed climbing to 1.7-2.5GiB (roughly
25-35% of the box's total 7.5GiB RAM) during active torrent activity. `nas-01` (TerraMaster
F4-424) has only 8GiB RAM total shared across 18 containers, so this growth pushes the box into
swapping and heavy disk I/O contention (`wa` — I/O wait — observed as high as 45-90% in `vmstat`
during an active episode, versus a healthy baseline under 5%).

Because `qbittorrent`, Sonarr/Radarr/Lidarr/Bazarr, and everything else on the box share the same
disk and the same RAM, this shows up as **general slowness across the whole arr stack**, not just
qBittorrent — Radarr/Lidarr response times were observed climbing from single-digit milliseconds
to 1-6+ seconds during an episode, while still returning `200 OK` (degraded, not down). This is
easy to misdiagnose as a per-service problem when the actual cause is one container starving the
whole host.

It self-resolves *temporarily* if left alone (the crunch eases once `qbittorrent`'s own I/O settles),
but recurs — observed twice in the same day.

## Diagnosing it live

Don't restart anything before confirming this is actually what's happening — the box can also be
fine when a service merely *feels* slow (browser cache, DNS, one-off network blip). Check, in
order:

```bash
uptime                                    # load average — sustained high 1-min is the headline signal
free -h                                   # low "available", high swap usage
vmstat 1 5                                # 'wa' column — I/O wait; healthy is <5%, an episode is 45-90%
docker stats --no-stream qbittorrent      # memory usage — healthy is a few hundred MB, an episode is 1.5GB+
```

Then confirm actual user-facing impact rather than trusting the resource numbers alone — test the
real access path (`.lan` hostnames via AdGuard, not raw IP:port, since that's how services are
actually reached day-to-day):

```bash
for url in "http://sonarr.lan:8989/" "http://radarr.lan:7878" "http://lidarr.lan:8686/" "http://bazarr.lan:6767/series"; do
  curl -s -o /dev/null -w '%{http_code} in %{time_total}s\n' --max-time 20 "$url"
done
```

Healthy is single-digit-to-low-double-digit milliseconds across all four. Anything crossing into
seconds, while still returning `200`, confirms the degradation pattern above rather than a crashed
service (check `docker ps` for restart loops / non-`Up` status separately — that's a different
problem with a different fix).

## The mitigation (not a fix)

```bash
docker restart -t 30 qbittorrent
```

Run from `nas-01` directly (SSH as `nexus-tnas` — see [SSH](../getting-started/ssh.md) for why
`kazuki` doesn't work here). Use `-t 30` (or higher) rather than the default: under real
contention, a plain `docker restart` can itself hang past Docker's default grace period without
completing — observed taking 90+ seconds under a severe episode, and completing in under a second
once the box wasn't as deeply wedged. Give it real room rather than assuming it failed.

Give it 30-60 seconds after the restart before re-testing — memory legitimately re-spikes
immediately post-restart (re-init, VPN/port-forward re-sync via Gluetun) before settling to a
normal footprint. Re-run the `.lan` curl checks above to confirm the whole stack recovered, not
just qBittorrent itself.

## Why this isn't fully fixed

This is a capacity problem, not a misconfiguration — no oversized disk-cache setting was found in
`qBittorrent.conf`; the growth is consistent with libtorrent 2.x's default mmap-based disk I/O for
whatever large media files are actively being handled, which is normal behavior, just expensive on
a box this tight on RAM. Restarting `qbittorrent` clears the immediate backlog but the box will
trend back toward the same pressure over time.

**The durable fix is a RAM upgrade.** The F4-424 has one SO-DIMM slot, factory-populated with 8GB
DDR5-4800 (not DDR4 — physically incompatible). It's a swap, not an addition. TerraMaster
officially supports up to 32GB in that slot (`A-SRAMD5-16G` / `A-SRAMD5-32G`, or equivalent
third-party DDR5-4800 SO-DIMMs). Not yet done as of this writing — restarting `qbittorrent` remains
the standing mitigation until the upgrade happens.
