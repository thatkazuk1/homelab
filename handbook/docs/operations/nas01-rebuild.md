# Operations: Rebuilding nas-01 from a blank TOS

This page is the procedure to bring `nas-01` (TerraMaster F4-424, TOS 7) from a fresh TOS install
to a full set of running stacks. It records what we did on 2026-10-24, after TOS refused to boot
(`apt dist-upgrade` changed a file that the TOS boot hash check protects).

!!! warning
    Do not run `apt upgrade` or `apt dist-upgrade` on TOS. TOS checks a hash of its system files at
    every boot. A package update changes those files, and the NAS beeps 3 times and stops. TOS
    updates come only from **Control Panel → System → Update**.

## What you get

| Item | Value |
|---|---|
| Address | `192.168.50.163`, DHCP reservation for the MAC of the bond |
| Network | `bond0`, LACP (802.3ad), two ports on the switch group `01` |
| Storage | One JBOD pool, 7.26 TB, Btrfs. **No redundancy.** |
| Volume | `Volume 1`, mounted at `/Volume1`. TOS fixes this name. |
| Shared folder | `data` (one Btrfs subvolume), with `media/` and `downloads/` inside |
| App state | `/Volume1/@apps/homelab/<stack>/` |
| SSH | Port `9222`, user `kazuki` (UID 0), key only |

Git keeps every compose file and every secret. The rebuild loses only the app state (the config
and the database of each app) and the media files.

## 1. Reinstall TOS

1. Use the RESET button on the motherboard to reinstall TOS. Follow the TerraMaster procedure for
   the F4-424. The NAS beeps 3 times and starts the TerraMaster Bootloader.
2. Find the NAS on the VLAN of the port that you used. The Bootloader and the setup wizard answer
   on that address.
3. In the wizard, create the superuser `kazuki` and set the device name `nas-01`. Store the password
   in your password manager. You can skip the security email, but then the RESET button is the only
   way back in.
4. After the wizard, open **Control Panel → System → Update** and install the latest TOS 7 release.
   Do this before you install any app.

## 2. Network: the LACP bond

1. On the switch (`swt-01`, D-Link `DGS-1210-28P`), the LAG group `01` (type LACP, ports 10 and 12)
   must exist. A reset of the NAS does not change the switch.
2. Keep the NAS on one cable first. In TOS, open **Control Panel → Network → Network Interface**,
   create a **Link Aggregation** of both ports, mode **IEEE 802.3ad**, address by **DHCP**.
3. Connect the two cables to switch ports 10 and 12.
4. The bond keeps the MAC of its first port. Add a Kea DHCPv4 reservation in OPNsense for that MAC
   and the address `192.168.50.163`. Restart the NAS to take the new lease.

!!! note
    The switch ports run at 1 Gbps, so the bond shows 2000 Mbps. One transfer uses one link and
    stays at 1 Gbps. The bond gives you a second path when a cable or a port fails.

## 3. Storage

1. Check the SMART data of both disks first (**Storage Manager → Disk → S.M.A.R.T.**). A pool
   without redundancy needs healthy disks. The values that matter: reallocated sectors, pending
   sectors and offline uncorrectable sectors. All must be 0.
2. Create the storage pool with the RAID mode **JBOD**, both disks. **RAID 0 is the default in the
   list. Do not confirm before you change it.** RAID 0 stripes the data, and one failed disk
   destroys everything on both disks.
3. Create the volume with the file system **Btrfs** and the full pool size. TOS names it
   `Volume 1`. A volume cannot be renamed.

JBOD has no redundancy. A disk failure loses the data on that disk. Keep a backup of anything that
you cannot download again.

## 4. SSH

1. **Control Panel → Terminal & SNMP:** turn on SSH, port `9222`.
2. **Control Panel → Security → Firewall:** add an **Allow** rule for TCP port `9222` from
   `192.168.30.0/24`. Without this rule, TOS drops the packets and gives no message.
3. Copy the key. The agent holds many keys, so tell `ssh` to use the password only:

   ```bash
   ssh-copy-id -o PubkeyAuthentication=no -i ~/.ssh/id_ed25519_nas01.pub -p 9222 kazuki@192.168.50.163
   ```

   Compare the fingerprint in the prompt with the output of
   `ssh-keyscan -p 9222 -t ed25519 192.168.50.163 | ssh-keygen -lf -`. Answer `yes` only if they match.
4. Make the home folder safe. TOS creates `/home/kazuki` with mode `777`, and `sshd` then ignores
   the key without a message. Log in with the password and run:

   ```bash
   chmod go-w ~
   ```

5. Set `PermitRootLogin prohibit-password` in `/etc/ssh/sshd_config` (the account is UID 0), run
   `sshd -t`, then `systemctl reload ssh.service`.
6. Remove the old host key of the address from `~/.ssh/known_hosts` with
   `ssh-keygen -R "[192.168.50.163]:9222"`.

## 5. The `data` shared folder

1. **Control Panel → Shared Folder:** create `data` on `Volume 1`. Leave the encryption off, the
   recycle bin off, and SMB, NFS and WebDAV off.
2. Open the permissions of `data` and give the group **`allusers`** the right **Read/Write**.

   !!! warning
       The volume is mounted with the `tmacl` option. For a TOS shared folder, the kernel checks the
       TOS permission entries and ignores the mode bits of a normal user. Without the group grant, a
       container that runs as UID 1006 cannot write, even in a folder with mode `777`. Folders
       outside a shared folder (such as `/Volume1/@apps`) use normal owner and mode rules.

3. Make the folders from the shell and give them to the UID that the containers use:

   ```bash
   mkdir -p /Volume1/data/media /Volume1/data/downloads
   chown 1006:997 /Volume1/data/media /Volume1/data/downloads
   chmod 775 /Volume1/data/media /Volume1/data/downloads
   ```

   The containers use `PUID=1006` and `PGID=997` (group `allusers`). No TOS user with the UID 1006
   exists, and none is needed. A container only needs the number. Do not create a TOS user later
   without a check: TOS can give it the UID 1006.

**Why one shared folder.** Each TOS shared folder is its own Btrfs subvolume. A hardlink or a fast
move between two subvolumes fails. With `media` and `downloads` inside one subvolume, and one mount
(`/Volume1/data` at `/data`) in the containers, an import of a finished download is a hardlink. It
takes no extra space.

## 6. Docker and Komodo Periphery

1. Install **Container Manager** from the App Center. The docker binary is then at
   `/Volume1/@apps/DockerEngine/dockerd/bin/docker`. It is not in the `PATH`.
2. Make the Periphery folders and files. Never print a secret:

   | Path under `/Volume1/@apps/homelab/komodo-periphery/` | Content |
   |---|---|
   | `compose.yml` | `stacks/komodo-periphery/compose.nas-01.yml` from this repo (check the `sha256sum`) |
   | `.env` | `PERIPHERY_CORE_PUBLIC_KEYS=...` (the public key of Komodo Core) |
   | `age-keys.txt` | The SOPS age key, mode `600`. Copy it from `nexus-v` and compare hashes. |
   | `docker-config/config.json` | The Docker Hub login, mode `600` |
   | `keys/` | Periphery makes its keypair here at the first start |

   Also create `/Volume1/@apps/komodo`.
3. The Periphery image comes from the Forgejo registry, which needs a login. Copy it from a host that
   already has it:

   ```bash
   ssh docker-prod-01 'docker save forgejo.ts.kazuki.uk/shokunbi/komodo-periphery-sops:2 | gzip -1' \
     | ssh nas-01 'gunzip | /Volume1/@apps/DockerEngine/dockerd/bin/docker load'
   ```

4. Start it: `docker compose -p komodo-periphery up -d` in the Periphery folder.
5. The new keypair is new to Komodo Core, and Core refuses it (`Failed to get handshake_m3`). In the
   Komodo UI, open **Servers → nas-01** and replace the pinned public key with the content of
   `keys/periphery.pub`. The server then shows **Ok**.

## 7. First deploy

The merge of any PR starts `deploy-all-changed`. It deploys only the stacks that changed. A stack
that did not change and has no containers stays `down`. After a rebuild, deploy these by hand with
Komodo (`DeployStack`): `beszel-agent`, `glances`, `hawser-nas-01`, `tracearr`, and any other
stack that shows `down`.

Rules that cost time on 2026-10-24:

- **Wait between calls.** `DestroyStack` returns at once and runs in the background. A
  `DeployStack` call right after it gets "Resource is busy". Wait until the stack leaves
  `deploying`, then call again.
- **Pull time.** The first pull of about 25 images takes 10 to 20 minutes. The `timescaledb`
  image of `tracearr` is the slowest.
- **Docker makes missing folders as root.** A container that has `user: "1006:997"` (`navidrome`,
  `jellyfin`, `seerr`) cannot write into such a folder and stops. The images that start as root and
  then change to `PUID` (the linuxserver images, `slskd`) fix this themselves. Before the first
  deploy, make the app folders and give them to `1006:997`:

  ```bash
  chown -R 1006:997 /Volume1/@apps/homelab/media /Volume1/@apps/homelab/jellyfin \
    /Volume1/@apps/homelab/navidrome /Volume1/@apps/homelab/slskd /Volume1/@apps/homelab/qBittorrent
  ```

- **`slskd` needs its download folders:** `mkdir /Volume1/data/downloads/torrents
  /Volume1/data/downloads/torrenting`, owner `1006:997`.
- **`gluetun` needs the file `config.toml` before the first start.** The compose file mounts
  `/Volume1/@apps/homelab/qBittorrent/config.toml`. If the file is missing, Docker makes a
  **directory** with that name, and `gluetun` stops with `config.toml: is a directory`. Docker also
  makes a stale directory `auth/config.toml` inside the named volume `qbittorrent_gluetun-data`. It
  survives `DestroyStack`. Remove it with `rmdir` in the volume path
  (`/Volume1/@apps/DockerEngine/DockerData/volumes/qbittorrent_gluetun-data/_data/auth/`).
- The file holds two roles (API keys). Take the key for the Homepage widget from
  `stacks/homepage/secrets.enc.env` (`HOMEPAGE_VAR_GLUETUN_API_KEY`) and the key for the port-sync
  add-on of `qbittorrent` from `stacks/qbittorrent/secrets.enc.env` (`GSP_GTN_API_KEY`). Write the
  file over SSH from the output of `sops exec-env`, so the keys are never printed:

  ```toml
  [[roles]]
  name = "homepage"
  routes = ["GET /v1/publicip/ip", "GET /v1/portforward"]
  auth = "apikey"
  apikey = "<HOMEPAGE_VAR_GLUETUN_API_KEY>"

  [[roles]]
  name = "port-sync"
  routes = ["GET /v1/portforward", "GET /v1/openvpn/portforwarded"]
  auth = "apikey"
  apikey = "<GSP_GTN_API_KEY>"
  ```

  Without the second role, the add-on gets `401` and the torrent port never reaches qBittorrent.

## 8. First-run settings of the apps

All apps start empty. The media files and the app state were lost in the wipe.

### qBittorrent

Stop `qbittorrent`, edit `qbittorrent/config/qBittorrent/qBittorrent.conf` in the stack folder,
then start it. qBittorrent overwrites the file when it exits, so edit only while it is stopped.
Set these keys (the paths in the file at first start point at `/downloads`, which no longer exists):

```ini
[BitTorrent]
Session\DefaultSavePath=/data/downloads/
Session\TempPath=/data/downloads/incomplete/
Session\DiskIOType=SimplePreadPwrite
Session\DisableAutoTMMByDefault=false

[WebUI]
LocalHostAuth=false
```

| Key | Why |
|---|---|
| `DefaultSavePath`, `TempPath` | The container has no `/downloads` mount now. A torrent would write into the container layer and fill the system partition. |
| `DiskIOType=SimplePreadPwrite` | Stops the memory growth of libtorrent 2.x. See [nas-01 arr stack performance](nas01-arr-performance.md). |
| `DisableAutoTMMByDefault=false` | Automatic Torrent Management. A category sets the save path. |
| `LocalHostAuth=false` | The port-sync add-on runs inside the container and calls the web interface on `localhost`. Without this, the add-on stops with "Init checks failed". |

Do **not** set the listening port by hand. The add-on writes the forwarded port of the VPN into
qBittorrent at each start. Check with the add-on log line "Qbittorrent port successfully updated".
At the first login, the temporary password is in the container log:
`docker logs qbittorrent 2>&1 | grep -i "temporary password"`. Run it in your own terminal, and set
a real password at once (**Tools → Options → Web UI**). Add the categories `tv`, `movies` and
`music` (**Categories**), with the save paths `/data/downloads/tv`, `/data/downloads/movies` and
`/data/downloads/music`.

### The arr apps

Inside the `media` stack, containers reach each other by service name on the network
`media-internal`. Other hosts and other stacks use `nas-01.lan` with the published port.

| App (port) | Setting |
|---|---|
| Sonarr (`8989`), Radarr (`7878`), Lidarr (`8686`) | **Media Management → Root Folders:** `/data/media/tv`, `/data/media/movies`, `/data/media/music`. Keep **Use Hardlinks instead of Copy** on. |
| Sonarr, Radarr, Lidarr | **Download Clients → qBittorrent:** host `nas-01.lan`, port `8080`, the qBittorrent user and password, category `tv`, `movies` or `music`. Test shows the check mark. |
| Prowlarr (`9696`) | **Settings → Apps:** add Sonarr (`http://sonarr:8989`), Radarr (`http://radarr:7878`) and Lidarr (`http://lidarr:8686`). Prowlarr server URL: `http://prowlarr:9696`. Take each API key from **Settings → General** of the app. |
| Prowlarr | **Settings → Indexers → Add proxy:** FlareSolverr, `http://flaresolverr:8191`, with a tag. Give the same tag to the indexers that need it. |
| Bazarr (`6767`) | **Settings → Sonarr / Radarr:** hosts `sonarr` and `radarr`, with the API keys. Bazarr mounts `/data/media`, so the paths match and no path mapping is needed. |
| Seerr (`5055`) | Sign in with Jellyfin (`http://nas-01.lan:8096`). Add Sonarr (`sonarr:8989`) and Radarr (`radarr:7878`) with the API keys and the root folders above. |
| Jellyfin (`8096`) | Libraries on `/data/media/tv`, `/data/media/movies`, `/data/media/music`. See `stacks/jellyfin/notes.md` for the anime libraries. |

Check the hardlink once from inside a container, as the app user:
`docker exec sonarr sh -c 'echo t > /data/downloads/.hl && ln /data/downloads/.hl /data/media/.hl && stat -c "%i %h" /data/downloads/.hl /data/media/.hl; rm -f /data/downloads/.hl /data/media/.hl'`.
Both names must show the same inode and the link count `2`.

## 9. After every restart of the NAS

Wait 3 to 5 minutes. Then check:

1. The restart policy of every container is not `no` (see
   [nas-01 after a restart or a power loss](nas01-slow-after-power-loss.md)).
2. `AllowUsers kazuki` and `PermitRootLogin prohibit-password` in `/etc/ssh/sshd_config`. The old
   system reset these lines at a restart. After the unplanned restart of 2026-10-24, TOS wrote the
   file again at boot and both lines held. Check anyway.
3. The firewall rule for TCP `9222` is still in **Control Panel → Security → Firewall**.
4. `gluetun` is healthy and `qbittorrent` runs.

## Known limits

- **No redundancy.** A failed disk loses its data. There is no mirror and no hot spare.
- **The pool has no NFS share for Proxmox.** The old `nexus-pve` share is gone. Proxmox storage
  entries that point at it stay dead until you create a new share and add a new entry.
- **Single stream speed is 1 Gbps** because of the switch.
