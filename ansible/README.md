# ansible/

Configuration management (L2), using role-based playbooks against hosts reached over the
per-host SSH keys documented in `handbook/docs/getting-started/ssh.md`.

**Status:** foundation only — one group (`scratch`), proven against a single throwaway guest.
Bringing the existing fleet under management is a later phase; provisioning guests via
OpenTofu is a separate, later phase too (`tofu/` stays empty until then).

## Structure

- `inventory/hosts.yml`, `inventory/group_vars/`, `inventory/host_vars/` — `group_vars`/
  `host_vars` live *inside* `inventory/`, not at the `ansible/` top level: Ansible only
  auto-loads them from a directory adjacent to the inventory file (or the playbook), and a
  flat top-level `ansible/group_vars/` is silently ignored given this layout — confirmed live
  when `hawser_token` came up undefined despite being set there.
- `roles/docker` — installs Docker CE from the official DEB822 `.sources` repo, trixie suite
- `roles/periphery` — deploys `komodo-periphery-sops:2`, including placing the fleet's age
  private key on the target (see `roles/periphery/defaults/main.yml` for why this can't be
  sops-encrypted at rest) and logging in to the private Forgejo registry first (credential in
  `stacks/komodo-periphery/secrets.enc.env`, a new file — this stack had no secrets before)
- `roles/hawser` — deploys the Hawser agent; the token is host-specific and secret, supplied
  via `group_vars`/`host_vars` (real hosts, sops-encrypted) or `-e` at the CLI (scratch/test)
- `playbooks/provision-baseline.yml` — runs all three roles against the `scratch` group

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
