# Operations: nas-01 is slow after a power loss

If `nas-01` crawls after a power loss or a hard reset, check for a RAID resync first.
A resync on the data array runs for about 2 days and slows every container.

## Symptoms

- The host rebooted without a clean shutdown (power loss or hard reset).
- Load average stays high for hours after the containers start.
- `vmstat` shows 70% to 85% I/O wait (`wa`), and swap use grows.
- Sonarr, Radarr, Lidarr and Bazarr answer in seconds, not milliseconds.
- No single process uses much CPU or disk.

## Cause

The data array `md0` is a RAID1 mirror (`sda4` and `sdb4`, 3.7 TB). After an unclean shutdown, the
kernel marks the array "not clean" and starts a full background resync. This is the kernel message:

```text
md/raid1:md0: not clean -- starting background reconstruction
```

Two facts make this worse on `nas-01`:

| Fact | Effect |
|---|---|
| `md0` has no write-intent bitmap (`md8` and `md9` have one). | The kernel cannot find the dirty blocks. It resyncs the whole 3.7 TB. |
| TOS sets `speed_limit_min` to 100000 KB/s (the kernel default is 1000). | The kernel guarantees the resync 100 MB/s, even when containers need the disk. |

The two disks cannot give 100 MB/s to the resync and to the containers together. The resync wins,
and the containers wait.

## Diagnose

Run these commands as `nexus-tnas` on `nas-01`. See [SSH](../getting-started/ssh.md) for the access
details.

```bash
cat /proc/mdstat                                  # look for "resync = NN%" on md0
cat /proc/sys/dev/raid/speed_limit_min            # 100000 means TOS default
dmesg | grep -i "not clean"                       # confirms the unclean shutdown
```

A healthy array shows `[UU]`. A resync is not a disk failure. If `[U_]` or `[_U]` appears, a disk
dropped out. That is a different problem.

## Fix: let the containers use the disk

> **Warning:** This setting lasts until the next reboot. The resync then takes longer, and the array
> has no verified redundancy until the resync ends. Both disks must show `[UU]` before you do this.

```bash
echo 1000 > /proc/sys/dev/raid/speed_limit_min
```

The resync still uses all idle disk time. It slows down only when containers need the disk.

Measured on 2026-10-20, 20 minutes after a power loss, 90 seconds after the change:

| Measure | Before | After |
|---|---|---|
| Load average (1 minute) | 18.35 | 7.98 |
| I/O wait | 84% | 36% to 49% |
| Radarr response | 4.5 s | 0.018 s |
| Lidarr response | 7.0 s | 0.023 s |

The resync continued at about 25 MB/s and needed about 34 more hours. To undo the change, run
`echo 100000 > /proc/sys/dev/raid/speed_limit_min`.

## Check the containers after the reboot

Wait 3 to 5 minutes after the reboot before you judge the containers. Docker starts about 90
seconds after the kernel, and the containers start one by one.

After a power loss, some containers can have `RestartPolicy=no`. They stay stopped. Check every
container:

```bash
for c in $(docker ps -aq); do docker inspect "$c" --format '{{.Name}} {{.HostConfig.RestartPolicy.Name}}'; done | grep -v always
```

On `nas-01` the `docker` binary is `/Volume1/@apps/DockerEngine/dockerd/bin/docker`. It is not in
the default `PATH`.

Recreate each stopped container from its stack directory with `--force-recreate`. A plain
`docker compose up -d` keeps the broken policy.

## Prevent a repeat

Both actions are open. Neither is done yet.

1. **Add a write-intent bitmap to `md0`.** With a bitmap, a resync after a power loss takes
   minutes, not 2 days. Run `mdadm --grow --bitmap=internal /dev/md0` after the current resync
   ends. This changes array metadata. Verify that TOS accepts it before you run the command.
2. **Install a UPS (uninterruptible power supply).** A UPS gives the NAS time for a clean shutdown.
   Then the array is never marked "not clean".

If the load stays high after the resync ends, see
[nas-01 arr stack performance](nas01-arr-performance.md). That page covers `qbittorrent` memory
growth.
