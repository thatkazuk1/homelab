# Operations: Deploying a new host

The playbook for bringing a new host into the fleet — from a booted machine to a
Komodo-managed Docker target. Proven across eight hosts so far (five Proxmox CTs in one
rollout, plus `docker-prod-01`, `core-01`, and `nas-01` individually). This page covers the
common path; `core-01` (Raspberry Pi) and `nas-01` (TerraMaster NAS) diverge at a few specific
steps, called out inline.

## 1. Provisioning

Most of the fleet is a Proxmox CT or VM, cloned from a Debian 13 template. For an unprivileged
LXC container that will run Docker, two options matter at creation time: `nesting=1` and
`keyctl=1` — without them, Docker inside the container won't start cleanly. Allocate a
`.lan`-range IP and a hostname following the `role-env-index` convention (see
[Conventions](../conventions/index.md)) before moving on.

Bare-metal hosts (`core-01`, `nas-01`) skip this step entirely — they're standardised in
place rather than provisioned from a template. `core-01` in particular is cloud-init managed;
its hostname lives in `/boot/firmware/user-data`, not settable via a plain `hostnamectl` (that
gets silently reverted on next boot).

## 2. Baseline configuration

Every host gets the same account shape (see [Conventions](../conventions/index.md)):

- **`kazuki`** — UID 1001, passwordless `sudo`, the interactive admin account. SSH key added
  to `~/.ssh/authorized_keys` via whatever bootstrap access exists first (the Proxmox
  console for a fresh CT/VM).
- **`svc-docker`** — a system account/group that group-owns stack data directories. This has
  been missed during initial provisioning more than once — worth checking explicitly
  (`getent group svc-docker`) rather than assuming it exists, and creating it at a consistent
  GID with the rest of the fleet if it doesn't.

Install Docker, then harden SSH: `PermitRootLogin prohibit-password`, `kazuki` as the only
interactive login path. See [Getting Started: SSH](../getting-started/ssh.md) for the
per-host-key convention this fleet uses for the workstation side of that connection.

Create the stack directory root (`/opt/homelab/` on Debian/LXC hosts, `nas-01`'s
`/Volume1/@apps/homelab/` equivalent), owned `kazuki:svc-docker`, setgid on the parent so
new stack directories inherit group ownership automatically.

**Unprivileged LXC containers have no `/dev/net/tun`** — if this host will run Tailscale,
it needs `--tun=userspace-networking`, not the default mode.

## 3. Register in Beszel

Deploy a `beszel-agent` container pointed at the fleet's Beszel hub (see
[`beszel`](../stacks/beszel.md)) so the new host shows up in fleet-wide monitoring. Confirm
it's actually reporting in the hub UI, not just running — agent presence and hub-side
reporting have drifted apart before on this fleet, so don't assume one implies the other.

## 4. Deploy Komodo Periphery

1. **Confirm the host's CPU architecture before pulling anything** — `uname -m`. This fleet
   is mostly `amd64` with one `arm64` exception (`core-01`); pulling the wrong architecture's
   image silently produces binaries that fail with `exec format error` at runtime, not at
   pull time.
2. Place the fleet's global age key at `/home/kazuki/.config/sops/age/keys.txt` (or the
   `nas-01`-style exception path if the host's filesystem doesn't support that layout) —
   Periphery's SOPS decryption depends on this being present *before* first deploy.
3. Deploy the custom Periphery image
   (`forgejo.ts.kazuki.uk/shokunbi/komodo-periphery-sops:2`, multi-arch) using the fleet's
   standard compose file, with an explicit `container_name: komodo-periphery`.
4. Confirm the container is actually running the architecture you expect —
   `docker exec komodo-periphery uname -m` should say `aarch64` on `core-01`, `x86_64`
   elsewhere. Don't rely on `docker image inspect`'s reported platform alone; it can match
   correctly while the binaries baked into a given image tag are still wrong for that arch (a
   real bug this fleet hit and fixed once already).

## 5. Register the server in Komodo Core

Operator-performed UI step, per [ADR-0013](../decisions/index.md) — the executor supplies the
exact values (host name, registration address), the operator clicks it into Komodo, the
executor verifies the result over SSH afterward.

- **Address:** `https://<HOST-IP>:8120` — **not** `http://`. Periphery has defaulted to SSL
  enabled (self-signed cert, auto-generated on first boot) since Komodo v1.15; `http://`
  registration fails silently against a host running this default.
- Confirm green status, and confirm the container list Komodo reports for the new host
  matches what's actually running (`docker compose ls` / `docker ps -a` on the host itself) —
  don't take Komodo's dashboard as the sole source of truth for what's live.

## 6. Optional: expose services

If this host will run something that needs to be reachable beyond itself, add a Traefik
router (on `proxy-prod-01`) and/or an AdGuard `.lan` DNS rewrite, per the
[DNS tier](../conventions/index.md#dns-tiers) that fits the service. Not every host needs
this — plenty of fleet hosts are reachable only via their bare `.lan` IP and that's
sufficient.

## What this doesn't cover yet

This playbook is currently a manual, per-host sequence — there's no L1/L2 automation
(OpenTofu/Ansible) driving it end-to-end. Each step above has been executed by hand at least
once; none of it is scripted yet. Treat this page as the checklist, not as a promise that any
part of it runs itself.
