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

## Recovering from a locked-out key

If a host becomes unreachable over SSH — a bad `sshd_config` change, a key rotation gone
wrong — the recovery path depends on what kind of host it is:

- **Proxmox guests (CTs/VMs)** — the Proxmox web UI's console gives direct terminal access to
  the guest without going through SSH at all.
- **`nas-01`** — has no persistent SSH story to fall back on in the first place. TOS
  (TerraMaster's OS) rewrites `sshd_config` on reboot or certain panel interactions, and
  `sudo` from non-`nexus-tnas` accounts resolves to a neutralised placeholder UID, not real
  root. The reliable path here is TOS's own browser-based Terminal app, not SSH recovery.
- **`core-01`** (Raspberry Pi) — no SSH-independent console exists by default. Recovery means
  physical access: pull the SD card and edit files directly, or attach a monitor and
  keyboard. Worth knowing this before you need it, since it means locking yourself out of
  `core-01` is more expensive to recover from than locking yourself out of a Proxmox guest.
