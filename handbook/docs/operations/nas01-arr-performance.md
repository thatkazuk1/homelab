# Operations: nas-01 arr stack performance degradation

What to do when Sonarr/Radarr/Lidarr/Bazarr (or the wider arr stack on `nas-01`) become slow or
unreachable, without necessarily being crashed.

!!! note
    If `nas-01` restarted in the last hour, wait 5 minutes and check the containers first. See
    [nas-01 after a restart or a power loss](nas01-slow-after-power-loss.md).

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

Run from `nas-01` directly (`ssh nas-01`, user `kazuki` — see [SSH](../getting-started/ssh.md)). Use `-t 30` (or higher) rather than the default: under real
contention, a plain `docker restart` can itself hang past Docker's default grace period without
completing — observed taking 90+ seconds under a severe episode, and completing in under a second
once the box wasn't as deeply wedged. Give it real room rather than assuming it failed.

Give it 30-60 seconds after the restart before re-testing — memory legitimately re-spikes
immediately post-restart (re-init, VPN/port-forward re-sync via Gluetun) before settling to a
normal footprint. Re-run the `.lan` curl checks above to confirm the whole stack recovered, not
just qBittorrent itself.

## What fixed it

The growth came from the default disk I/O mode of libtorrent 2.x, which maps files into memory.
Two changes stop it:

1. **Disk IO type.** In qBittorrent the setting is `Simple pread/pwrite`. The key in
   `qBittorrent.conf` is `Session\DiskIOType=SimplePreadPwrite`. With this setting, `qbittorrent`
   uses about 30 to 90 MiB. Before the change it grew to 1.5 to 2.5 GiB.
2. **Memory cap.** The compose file sets `mem_limit: 3g` and `memswap_limit: 3g` for `qbittorrent`.
   If it ever grows again, the kernel stops only this container and not the whole host.

After a rebuild of `nas-01`, the qBittorrent config is new, and the Disk IO type is the default
again. [Rebuilding nas-01](nas01-rebuild.md) lists the keys to set in the config file.

Check the cap after every recreate of `qbittorrent`:

```bash
docker inspect qbittorrent --format 'mem={{.HostConfig.Memory}} swap={{.HostConfig.MemorySwap}}'
```

Both values must be `3221225472`. On 2026-10-21 the running container had `mem=0`, although the
compose file had the limit. Docker applies limits on this host, so the container was created
without them. Recreate only this service to restore the cap. From the stack directory, run
`docker compose -p qbittorrent -f compose.yml up -d --force-recreate --no-deps qbittorrent`. Run it
through `komodo-periphery` with `sops exec-env secrets.enc.env`. Do not recreate `gluetun`.

A RAM upgrade is not the main fix now. It stays an option if memory pressure returns. The F4-424 has
one SO-DIMM slot with 8GB DDR5-4800. DDR4 does not fit. A new module replaces the old one. TerraMaster
supports up to 32GB in that slot (`A-SRAMD5-16G` or `A-SRAMD5-32G`, or an equal third-party DDR5-4800
SO-DIMM).
