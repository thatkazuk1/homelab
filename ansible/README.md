# ansible/

Configuration management (L2), using role-based playbooks against hosts reached over the
per-host SSH keys documented in `handbook/docs/getting-started/ssh.md`.

**Status (Sprint 4b/4c):** the real fleet is under management. `docker_hosts` (8 real hosts)
runs the Docker + Periphery baseline; live-rolled-out and verified (byte-identical container
IDs/timestamps before and after, idempotent re-`--check`) on 7 of 8 — `forgejo-prod-01`'s
Periphery install is blocked on a Forgejo registry token scope issue, an operator/UI action,
not a role bug (directory/.env/compose/login all applied for real; the image pull itself
401s, no container created). `komodo-prod-01` gets `periphery_managed: false` — its Periphery
is a fundamentally different deployment shape (vanilla image bundled inside the `komodo`
stack's own compose, not `-sops`, not at the standard path) and is deliberately left
untouched rather than parameterized. `scratch` remains a throwaway group for proving new role
work end-to-end (including `hawser`, which is out of real-fleet scope for now, per operator
decision — see the Sprint 4b status report) before touching real hosts. Proxmox node baking
(`roles/proxmox_node`, Sprint 4c) is config-validated only — `ansible-lint`/`--syntax-check`
pass, but no node has ever booted from it; see `proxmox-node-baking/README.md`. Provisioning
guests via OpenTofu is a separate, later phase (`tofu/` stays empty until then).

## Structure

- `inventory/hosts.yml` — one group per real fleet role: `docker_hosts` (all 8 Proxmox-guest
  Docker hosts) and `scratch` (a throwaway test guest, not a real fleet host). Per-host
  exceptions live in `host_vars`, not as separate groups.
- `inventory/group_vars/`, `inventory/host_vars/` — live *inside* `inventory/`, not at the
  `ansible/` top level: Ansible only auto-loads them from a directory adjacent to the
  inventory file (or the playbook), and a flat top-level `ansible/group_vars/` is silently
  ignored given this layout — confirmed live when `hawser_token` came up undefined despite
  being set there. Real per-host drift (directory modes, file group ownership, host-local
  `.env` exceptions) is captured here rather than normalized away — see the comments in each
  `host_vars/<host>.yml` file for what's genuine fleet divergence vs. role defaults.
- `roles/docker` — installs Docker CE from the official DEB822 `.sources` repo, trixie suite
- `roles/periphery` — deploys `komodo-periphery-sops:2`, including placing the fleet's age
  private key on the target (see `roles/periphery/defaults/main.yml` for why this can't be
  sops-encrypted at rest) and logging in to the private Forgejo registry first (credential in
  `stacks/komodo-periphery/secrets.enc.env`). `periphery_managed: false` (host_vars) skips the
  role entirely for hosts whose Periphery is a fundamentally different shape (`komodo-prod-01`).
- `roles/hawser` — deploys the Hawser agent; the token is host-specific and secret, supplied
  via `group_vars`/`host_vars` (real hosts, sops-encrypted) or `-e` at the CLI (scratch/test).
  Not currently run against any real fleet host (see Status above).
- `roles/proxmox_node` — post-install baseline for a freshly auto-installed Proxmox node
  (repo config, Netdata, Beszel agent, `kazuki` NOPASSWD sudo finalization, cluster join).
  Written and statically validated only; see `proxmox-node-baking/README.md` for the honest
  proven-vs-not boundary. No `proxmox_nodes` inventory group exists yet — `pve-01`/`pve-02`
  are live production and don't match this role's fresh-node assumptions.
- `playbooks/provision-baseline.yml` — two plays: `docker` + `periphery` against
  `docker_hosts` (the real fleet baseline); `docker` + `periphery` + `hawser` against
  `scratch` (the end-to-end proof path, hawser included there only).
- `playbooks/provision-proxmox-node.yml` — `proxmox_node` role against `proxmox_nodes`
  (currently empty; first real run is first real hardware, a future sprint).

## Running

```bash
cd ansible
ansible-galaxy collection install -r requirements.yml
ansible-playbook playbooks/provision-baseline.yml --check   # idempotence check
ansible-playbook playbooks/provision-baseline.yml
```

## Secrets

Uses `community.sops` — its lookup plugin reads a sops-encrypted file directly (age identity
resolves at the XDG default, `~/.config/sops/age/keys.txt`, same as the `sops` CLI). See
`ansible/inventory/group_vars/scratch.yml` for the exact lookup syntax used against
`stacks/hawser/secrets.enc.env`, and `ansible/roles/periphery/tasks/main.yml` for the same
pattern against `stacks/komodo-periphery/secrets.enc.env` (Forgejo registry pull credential —
needed because a freshly-provisioned host has never run `docker login` against the private
registry the Periphery image lives in; nothing in the existing per-host runbook documented
this step, so it was a real gap this sprint surfaced, not an oversight in this role).

No new `.sops.yaml` creation rule was needed for `ansible/`-adjacent secrets — the existing
rule (`\.enc\.(yaml|yml|json|env)$`) is unanchored at the start, so it already matches any
path ending that way regardless of directory. Verified with a round-trip test-encrypt.
