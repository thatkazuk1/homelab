# Operations: nas-01 after a restart or a power loss

Use this page after `nas-01` restarted, with or without a clean shutdown. It covers the checks
that find a stopped container, and it records what a power loss does and does not do on this
system.

## What changed on 2026-10-24

Before the rebuild, the data array `md0` was a RAID1 mirror without a write-intent bitmap. After a
power loss, the kernel resynced all 3.7 TB for many hours, and every container waited for the
disk. That problem is gone. `md0` is now a `linear` array (JBOD) over both disks, and a linear
array has no resync.

A power loss can still do harm:

- Btrfs recovers its own state at the next mount, but a file that was in the middle of a write can
  stay damaged. A torrent recheck repairs a download.
- There is no mirror. A disk that fails after a power loss loses its data. See
  [Rebuilding nas-01](nas01-rebuild.md).
- The small system arrays `md8` and `md9` are still RAID1 with a bitmap and recover in seconds.

## Symptoms

- The host restarted (power loss, hard reset or an update).
- Many containers stay stopped (`Exited (255)`) one minute after the start.
- A container that joins the network of another container (`qbittorrent` on `gluetun`) stays
  `Created`.

## Check the containers

Wait 3 to 5 minutes after the restart before you judge the containers. Docker starts about 90
seconds after the kernel, and the containers start one by one.

The `docker` binary is not in the default `PATH` on `nas-01`:

```bash
DOCKER=/Volume1/@apps/DockerEngine/dockerd/bin/docker
$DOCKER ps -a --format '{{.Names}}|{{.Status}}' | sort
for c in $($DOCKER ps -aq); do $DOCKER inspect "$c" --format '{{.Name}} {{.HostConfig.RestartPolicy.Name}}'; done | grep ' no$'
```

The second command lists every container with the restart policy `no`. A container with this
policy stays stopped after a restart. On `nas-01` the policy of many containers reset to `no`
after a restart in the past (2026-09-12 and 2026-10-20: all 23 containers).

On 2026-10-24, five containers showed `no` one minute after an unplanned restart. A few minutes
later the same containers showed `always`. Check again after 5 minutes before you change anything.

If a container keeps the policy `no`:

1. Set the policy on every container. This command does not recreate the containers.

   ```bash
   for c in $($DOCKER ps -aq); do $DOCKER update --restart=unless-stopped "$c"; done
   ```

2. Start `gluetun`. Wait until `$DOCKER inspect gluetun --format '{{.State.Health.Status}}'` shows
   `healthy`.
3. Start `qbittorrent`, `komodo-periphery`, `autoheal` and the other stopped containers. Use
   `$DOCKER ps -a` to list them.

> **Warning:** Do not recreate `gluetun` alone. The `qbittorrent` container joins the network of
> one specific `gluetun` container. If `gluetun` is recreated, `qbittorrent` fails to start with
> `No such container`. Recreate `qbittorrent` after it.

A `docker compose up -d --force-recreate <service>` from the stack directory also restores the
policy. A plain `docker compose up -d` does not.

## If `gluetun` does not start

| Log line or error | Cause | Fix |
|---|---|---|
| `config.toml: is a directory` | The file `/Volume1/@apps/homelab/qBittorrent/config.toml` is missing, and Docker made a directory. | Remove the directory, write the file. See [Rebuilding nas-01](nas01-rebuild.md), section 7. |
| `error mounting ... not a directory` at `docker start` | A stale directory `auth/config.toml` exists inside the volume `qbittorrent_gluetun-data`. | `rmdir` it in the volume path, then start `gluetun`. |
| `401` lines for `/v1/openvpn/portforwarded`, and the add-on does not set the port | The file `config.toml` has no role for the key `GSP_GTN_API_KEY`. | Add the `port-sync` role. |

## Check SSH

After a restart, check these on `nas-01`:

```bash
grep -E '^(AllowUsers|PermitRootLogin)' /etc/ssh/sshd_config   # AllowUsers kazuki, PermitRootLogin prohibit-password
```

The firewall rule for TCP `9222` is in **Control Panel → Security → Firewall**. The old system lost
the `AllowUsers` entry at each restart. After the restart of 2026-10-24, TOS wrote the file again at
boot, and the entries held.

If the NAS is slow after the containers are up, see
[nas-01 arr stack performance](nas01-arr-performance.md). That page covers `qbittorrent` memory
growth.
