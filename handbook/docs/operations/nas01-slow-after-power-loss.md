# Operations: nas-01 is slow after a power loss

If `nas-01` crawls after a power loss or a hard reset, check for a RAID resync first.
A resync on the data array runs for many hours and slows every container.

## Symptoms

- The host rebooted without a clean shutdown (power loss or hard reset).
- Load average stays high for hours after the containers start.
- `vmstat` shows 70% to 85% I/O wait (`wa`), and swap use grows.
- Sonarr, Radarr, Lidarr and Bazarr answer in seconds, not milliseconds.
- No single process uses much CPU or disk.
- After the reboot, many containers stay stopped. See
  [Check the containers after the reboot](#check-the-containers-after-the-reboot).

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

The resync continued at about 25 MB/s. To undo the change, run
`echo 100000 > /proc/sys/dev/raid/speed_limit_min`.

The first kernel estimate was about 45 hours. The resync that I observed ended 13.5 hours after the
first boot (`md: md0: resync done.` in `dmesg`), with a second outage in the middle. The speed
changes with the load, so the estimate is not reliable. The setting `speed_limit_min` returns to
100000 at every reboot, because TOS sets it again.

## Check the containers after the reboot

Wait 3 to 5 minutes after the reboot before you judge the containers. Docker starts about 90
seconds after the kernel, and the containers start one by one.

After a power loss, the restart policy of the containers can reset to `no`. A container with this
policy stays stopped. On 2026-10-20, all 23 containers had the policy `no` after the second
outage. This included containers that were recreated earlier the same day. The cause is not
confirmed.

The `docker` binary is not in the default `PATH` on `nas-01`. Set a variable for it, then check
every container:

```bash
DOCKER=/Volume1/@apps/DockerEngine/dockerd/bin/docker
for c in $($DOCKER ps -aq); do $DOCKER inspect "$c" --format '{{.Name}} {{.HostConfig.RestartPolicy.Name}}'; done | grep ' no$'
```

Restore the policy and start the containers in this order:

1. Set the policy on every container. This command does not recreate the containers.

   ```bash
   for c in $($DOCKER ps -aq); do $DOCKER update --restart=unless-stopped "$c"; done
   ```

2. Start `gluetun`. Wait until `$DOCKER inspect gluetun --format '{{.State.Health.Status}}'` shows
   `healthy`. This took 10 seconds.
3. Start `qbittorrent`, `komodo-periphery`, `autoheal` and the other stopped containers. Use
   `$DOCKER ps -a` to list them. Do not forget any container.

> **Warning:** Do not recreate `gluetun` alone. The `qbittorrent` container joins the network of one
> specific `gluetun` container. If `gluetun` is recreated, `qbittorrent` fails to start with
> `No such container`. Recreate `qbittorrent` after it.

A `docker compose up -d --force-recreate <service>` from the stack directory also restores the
policy. A plain `docker compose up -d` does not. The policy can reset again at the next reboot, so
check it after every reboot.

## Prevent a repeat

Two actions prevent a long resync. Status on 2026-10-21: neither is applied.

### Write-intent bitmap on `md0`

A write-intent bitmap is safe to add to `md0`. After a power loss, the kernel then resyncs only the
regions that changed. This takes minutes, not hours. The bitmap does not speed up the rebuild after
you replace a disk.

The mdadm manual states that a bitmap can be added to an active array. The internal bitmap lives in
the array metadata, on all member disks. These are the checks on `nas-01`:

| Check | Result |
|---|---|
| Versions | `mdadm` v4.0 and kernel 6.12.63. A bitmap needs `mdadm` 2.1 and kernel 2.6.14 or later. |
| Space | `md0` has metadata 1.2 and a data offset of 128 MiB. About 128 MiB is unused before the data. A bitmap with 64 MiB chunks needs about 7.4 KiB. |
| State | `md0` is `clean` and `[UU]`. Both members show the same event count. |
| TOS arrays | `md8` and `md9` already have a bitmap with 64 MiB chunks, 8 sectors after the superblock. TOS made them. |
| Effect | After the first boot on 2026-10-20, `md9` recovered in 5 seconds and `md8` in 1 second. `md0` needed a full resync. |
| TOS config | `/etc/mdadm/mdadm.conf` lists the arrays and has no bitmap option. TOS rewrites the file. The bitmap needs no entry. |

Costs and limits:

- Writes can be slower. An old kernel wiki reports up to about 10%, and usually less. Long
  sequential writes are affected most.
- You cannot change the array size while a bitmap is active. Before you grow the array, for example
  after a swap to larger disks, remove the bitmap. Grow the array, then add the bitmap again.
- I found no TOS script that removes a bitmap. `TOSDaemon` is a compiled program, and I could not
  read its code. After any array change in the TOS GUI, check that the bitmap is still present.

Run these commands as `nexus-tnas` on `nas-01`. Use them only when `md0` is `clean` and no resync
runs:

```bash
mdadm --grow --bitmap=internal /dev/md0
cat /proc/mdstat                              # md0 shows a "bitmap:" line
mdadm --examine /dev/sda4 | grep -i bitmap    # shows an "Internal Bitmap" line
```

The change needs no unmount and no downtime. It does not move data. To undo it, run
`mdadm --grow --bitmap=none /dev/md0`. After the next reboot, check `cat /proc/mdstat` again.

### UPS (uninterruptible power supply)

A UPS gives the NAS time for a clean shutdown. Then the array is never marked "not clean". TOS has
UPS support: a TOS message states that the device shuts down automatically when the battery level
reaches the threshold.

If the load stays high after the resync ends, see
[nas-01 arr stack performance](nas01-arr-performance.md). That page covers `qbittorrent` memory
growth.
