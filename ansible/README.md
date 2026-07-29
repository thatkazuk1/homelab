# ansible/

Configuration management (L2), using role-based playbooks against hosts reached over the
per-host SSH keys documented in `handbook/docs/getting-started/ssh.md`.

**Status:** foundation only (Sprint 4a) — one group (`scratch`), proven against a single
throwaway guest. Bringing the existing fleet under management is Sprint 4b; provisioning
guests via OpenTofu is Sprint 4d (`tofu/` stays empty until then).

## Structure

- `roles/docker` — installs Docker CE from the official DEB822 `.sources` repo, trixie suite
- `roles/periphery` — deploys `komodo-periphery-sops:2`, including placing the fleet's age
  private key on the target (see `roles/periphery/defaults/main.yml` for why this can't be
  sops-encrypted at rest)
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
`ansible/group_vars/scratch.yml` for the exact lookup syntax used against
`stacks/hawser/secrets.enc.env`.

No new `.sops.yaml` creation rule was needed for `ansible/` secrets — the existing rule
(`\.enc\.(yaml|yml|json|env)$`) is unanchored at the start, so it already matches any path
ending that way regardless of directory. Verified with a round-trip test-encrypt under
`ansible/` during Sprint 4a.
