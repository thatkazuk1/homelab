# proxmox/

A reusable, parameterized process for baking a fleet-standard Proxmox node
from the official ISO auto-installer (`answer.toml` + `prepare-iso`), plus
the bridge into Ansible configuration management. Sprint 4c — the
bare-metal analogue of 4a's guest-template baking.

**Status (Sprint 4c):** config-validated, not live-validated. `validate-answer`
and `prepare-iso` have been run for real against a filled example and
produce a real, unbooted ISO (see the sprint status report for captured
output). The first-boot hook and the post-install role
(`ansible/roles/proxmox_node/`) are written and statically validated
(shellcheck / ansible-lint / `--syntax-check`) only — **no node has ever
booted from this process.** Do not treat this directory as proof a node
can be provisioned end-to-end; that proof doesn't exist yet.

## Files

- `answer.toml.tmpl` — parameterized answer file. `{{ VARIABLE }}`
  placeholders (`HOSTNAME`, `FQDN_DOMAIN`, `MGMT_CIDR`, `DISK_FILTER`,
  `SSH_PUBKEY`, `ROOT_PASSWORD`) get substituted by `render-answer.sh`.
  Never fill this in by hand and commit the result.
- `answer.example.toml` — a filled example with placeholder host values
  and an obviously-fake password, committed so `validate-answer` has a
  real, static fixture to run against without needing SOPS or a real
  node identity. Not a template for a real install.
- `secrets.enc.env` — SOPS-encrypted `PROXMOX_ROOT_PASSWORD`, the real
  value `render-answer.sh` injects at fill time. Same `community.sops`/
  `sops` CLI pattern as every other `secrets.enc.env` in this repo
  (ADR-0008), even though this directory isn't a `stacks/` entry.
- `render-answer.sh` — fills the template (network/host values as CLI
  args, password from `secrets.enc.env`) and writes the result to
  `/tmp/answer.<hostname>.toml` (gitignored pattern, mode 600). Also
  renders `first-boot-hook.sh.tmpl` with the target pubkey substituted.
  Run this **on the trusted PVE node** that will run `prepare-iso` —
  see Prerequisites below.
- `first-boot-hook.sh.tmpl` — the `--on-first-boot` script template.
  Minimal by design: creates `kazuki` (UID 1001, sudo-group), installs
  the node's SSH pubkey, asserts `openssh-server`/`python3`. Real
  configuration is `ansible/roles/proxmox_node/`'s job, not this
  script's.

## Prerequisites (per node-baking session, not yet automated)

- `proxmox-auto-install-assistant` installed on the PVE node running
  `prepare-iso` (apt package, `pve-no-subscription` repo — confirmed
  available, candidate 9.2.7 as of Sprint 4c; **not installed on
  pve-01/pve-02 by default**, the operator installed it manually via
  interactive `sudo` for this sprint's dry-proof since `kazuki`'s sudo
  on `pve-01` prompts for a password non-interactively — see CLAUDE.md's
  documented exception).
- `sops` + `age`, with the fleet's age key at
  `~/.config/sops/age/keys.txt`, on that same trusted PVE node — **not
  currently true on pve-01/pve-02** (confirmed absent, Sprint 4c). This
  is a real gap: the "decrypt at prepare-iso time on the trusted PVE
  node" design assumes this exists. First real bake needs this step
  first (same first-time-setup shape as Sprint 3v's `forgejo-prod-01`
  SOPS install, a first outside the Periphery-container pattern).
- The PVE 9.2 ISO itself (`https://enterprise.proxmox.com/iso/proxmox-ve_9.2-1.iso`
  as of Sprint 4c — VERIFY current version at execution time). No local
  apt cache path (`/var/lib/vz/template/iso/`) write access for
  `kazuki` on pve-01/pve-02 (root-owned, `kazuki` not in the owning
  group) — downloaded to `/tmp` instead this sprint.
- A per-node SSH keypair generated on `nexus-v` by the operator (fleet's
  per-host key convention — see `handbook/docs/getting-started/ssh.md`),
  pubkey fed to `render-answer.sh`.

## Fleet reality this template encodes (Sprint 4c, Phase 0 audit)

Captured live from `pve-01`/`pve-02`, not assumed:

- **Network**: static (`from-answer`), single physical NIC → `vmbr0`
  bridge, no VLAN, `/24`, gateway `192.168.50.1`, DNS `192.168.50.3`
  (`core-01`'s AdGuard). No bonding, no multi-NIC ambiguity on either
  existing node.
- **Locale**: `en_US.UTF-8` / keyboard `en-us` — **not** `en_NG.UTF-8`,
  which is what the Sprint 4a VM template uses. Don't cross-apply that
  guest-template assumption here; confirmed independently via
  `locale -a` on both PVE nodes.
- **Timezone**: `Africa/Lagos` — consistent with the VM template.
  `country = "ng"` is inferred from this (best-effort; no single PVE
  config file states a country code directly).
- **Disk**: single physical disk per node (~256GB, `Samsung MZNLH...`
  model, exposed as `/dev/sda`), standard Proxmox-installer LVM-thin
  layout (EFI + `pve` VG: 8G swap, ~69G root ext4, thin-pool for
  VM/CT disks). Both existing nodes identical shape (same hardware
  SKU, Lenovo ThinkCentre M700 Tiny). `filter.ID_MODEL` is the
  parameterized disk filter — a size- or serial-based filter would
  also work; model was chosen since both current nodes share one.
- **Repo config**: `pve-no-subscription` enabled, `pve-enterprise` +
  `ceph` disabled. `ceph.sources` exists but disabled on both nodes
  with no evidence of deliberate configuration — read as installer
  default, not managed by `ansible/roles/proxmox_node/`.
- **Netdata**: native apt package (full plugin-suite metapackage,
  v2.10.3 as observed), via Netdata's own official kickstart script
  (`get.netdata.cloud/kickstart.sh`) rather than hand-replicated repo
  files — its signing key isn't something to maintain by hand here.
- **Beszel agent**: native binary (`/opt/beszel-agent/`), systemd
  units (`beszel-agent.service` + a daily `beszel-agent-update.timer`,
  confirming `--auto-update` was used at install), via Beszel's own
  official install script. **`KEY`/`TOKEN` are per-node, operator-issued
  credentials from the Beszel hub UI** — confirmed via SHA256 comparison
  of the two nodes' values (different hashes; no plaintext ever printed,
  per CLAUDE.md's secret-handling discipline) — not a fleet-shared
  secret. Same model as Hawser's token.
- **SSH**: per-host key convention confirmed (`kazuki@pve-01`/`kazuki@pve-02`
  comment on each node's `authorized_keys` entry, matching
  `id_ed25519_pve01`/`id_ed25519_pve02`). `PermitRootLogin
  prohibit-password`, no `AllowUsers` restriction.
- **A genuine discrepancy, not silently resolved**: `pve-01`'s own
  `/etc/hosts` FQDN domain (`pve.home`) doesn't match its own
  `/etc/resolv.conf` search domain (`pve1.home`) — `pve-02` is
  internally consistent (`pve2.home` in both). Each existing node
  appears to have its own per-node domain suffix rather than a shared
  cluster domain, and `pve-01` itself disagrees with itself about what
  that suffix is. `answer.toml.tmpl`'s `FQDN_DOMAIN` is left fully
  operator-supplied per node rather than guessing a `pve{N}.home`
  pattern — flagged for the operator to resolve/decide, not fixed here.
- **`kazuki` UID/sudo**: the hook creates `kazuki` at UID 1001 with
  NOPASSWD sudo (via the role) — the fleet's documented *standard*, not
  what `pve-01`/`pve-02` actually have today (UID 1000, non-NOPASSWD or
  no `sudo` binary at all — pre-standardization drift, previously
  flagged as a doc inaccuracy in Sprint 3i and still unresolved). This
  is a deliberate choice for new hardware, not a replication of the two
  existing nodes' state — flagged for operator confirmation.

## Not proven this sprint

`validate-answer` and `prepare-iso` are real, executed proofs (output
captured in the sprint status report). The first-boot hook and
`proxmox_node` role are **not executed** — no node exists to run them
against. Their idempotence and correctness against real hardware are
unproven. See the runbook's "Adding a new node" section
(`handbook/docs/runbooks/pve-cluster.md`) for the
config-validated-vs-live-pending split, and the Sprint 4c status report
for the full honesty-boundary statement.
