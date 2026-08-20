# Getting Started: SSH

Every host in the fleet is reached over SSH from `nexus-v` (the operator's workstation), the
one place all git operations and infrastructure changes originate. This page covers the
key setup and the reasoning behind it.

## Why per-host keys

Each host gets its own SSH keypair, rather than one key shared across the fleet. The
tradeoff is more keys to manage in exchange for a much smaller blast radius: if one host's
key is ever compromised, only that host's access is affected, and rotating it doesn't touch
anything else. It also makes `~/.ssh/config` self-documenting — the key name tells you which
host it's for.

## Generating a key

```bash
ssh-keygen -t ed25519 -C "kazuki@nexus-v -> docker-prod-01" -f ~/.ssh/id_ed25519_docker-prod-01
```

`ed25519` over RSA — smaller keys, faster verification, no known weaknesses at current key
sizes. The `-C` comment is just a label (shown in `authorized_keys` and `ssh-add -l`); make it
descriptive enough to identify at a glance. Protect the private key file itself — it never
leaves `nexus-v`, and a passphrase on it is worth the minor friction given what it can reach.

## `~/.ssh/config` structure

One `Host` block per fleet host, pinned to its specific key:

```
Host docker-prod-01
    HostName 192.168.50.105
    User kazuki
    IdentityFile ~/.ssh/id_ed25519_docker-prod-01
    IdentitiesOnly yes
```

`IdentitiesOnly yes` matters more than it looks — without it, `ssh-agent` will offer every
loaded key to the server in turn, which can trip a target's failed-attempt rate limiting
before it ever reaches the right key. Pinning `IdentityFile` and setting `IdentitiesOnly`
together means each host is only ever offered its own key.

## Getting a key onto a host

For a new host, the initial key lands via whatever bootstrap access exists first — the
Proxmox console for a freshly-provisioned CT/VM, or the vendor's own out-of-band mechanism for
bare metal. From there, `kazuki`'s `~/.ssh/authorized_keys` gets the new public key appended.
This is currently a manual step per host; when an L2 configuration-management layer (Ansible)
lands, distributing keys becomes one of its jobs rather than a by-hand step.

## Why no direct root SSH

`PermitRootLogin prohibit-password` is the standard on every host in this fleet — root can't
log in with a password, and in practice root doesn't log in directly at all. The pattern
instead is a `kazuki` user (UID 1001) with passwordless `sudo`: you SSH in as `kazuki`, then
`sudo` for anything that needs root. This keeps a real audit trail (commands run as `kazuki`
via `sudo`, not as an anonymous `root` session) without adding meaningful friction, since
`sudo` doesn't prompt for a password.

**`nas-01` is an exception to this pattern.** SSH there is as `nexus-tnas` (TOS's built-in
root-equivalent account, UID 0) directly, with `PermitRootLogin prohibit-password` — not
`kazuki` + `sudo`. This isn't the intended long-term state; it's a working fallback. See below
for why.

## Recovering from a locked-out key

If a host becomes unreachable over SSH — a bad `sshd_config` change, a key rotation gone
wrong — the recovery path depends on what kind of host it is:

- **Proxmox guests (CTs/VMs)** — the Proxmox web UI's console gives direct terminal access to
  the guest without going through SSH at all.
- **`nas-01`** — has no reliable SSH story for `kazuki` at all, and the recovery path is TOS's
  own browser-based Terminal app (login as `nexus-tnas`), not SSH. Two distinct, confirmed
  issues, not one: (1) TOS's own iptables chain (`INPUT_PROTECT`) silently drops inbound
  traffic to the SSH port from any subnet outside nas-01's own LAN, its Docker networks, and a
  Tailscale range — fixed per-source via Control Panel → Security → Firewall, an Allow rule
  for the connecting subnet on the SSH port; and (2) `sshd_config`'s `AllowUsers` line reverts
  to `nexus-tnas`-only on its own, on some undetermined trigger unrelated to GUI panel touches
  — `kazuki` gets silently dropped from it, and editing the file directly does not hold.
  Root cause of (2) is unconfirmed but circumstantially points at `TOSDaemon` (an always-running
  vendor process) reconciling system config from a local Postgres database it maintains
  (`postgres: terramaster tos`) — not yet investigated further. **Working access today is
  `nexus-tnas` (root-equivalent), not `kazuki`** — a key is staged at
  `/home/nexus-tnas/.ssh/authorized_keys` and `PermitRootLogin prohibit-password` is set,
  confirmed durable (unlike `AllowUsers` edits, which revert within seconds). `sudo` from
  non-`nexus-tnas` accounts still resolves to a neutralised placeholder UID, not real root, so
  this exception is specifically about SSH login identity, not a broader relaxation.
- **`core-01`** (Raspberry Pi) — no SSH-independent console exists by default. Recovery means
  physical access: pull the SD card and edit files directly, or attach a monitor and
  keyboard. Worth knowing this before you need it, since it means locking yourself out of
  `core-01` is more expensive to recover from than locking yourself out of a Proxmox guest.
