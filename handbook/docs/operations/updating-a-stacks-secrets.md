# Updating a Stack's Secrets

Applies when you need to change environment-variable values a stack consumes
at deploy time — credential rotation, service migration (like a bucket
rename), or fixing a mistake. This page covers stacks that use the
[SOPS-encrypted `secrets.enc.env` pattern](../decisions/0010-per-stack-sops-secrets.md).

## How secrets travel from repo to running container

<Brief mental model: encrypted file in git → sops exec-env at deploy time →
env vars in memory → docker compose picks them up → container reads them.
The age key on the Periphery host is what enables decryption.>

## The pattern

Six steps. Never skip step 4.

### 1. Understand what the stack references

Read `stacks/<name>/compose.yml` for the env var names. Confirm they exist
in the encrypted file:

```bash
sops -d stacks/<name>/secrets.enc.env | cut -d= -f1
```

This shows names only, not values.

### 2. Make the external change first

If you're rotating a credential, create the new one at the source (Garage,
API provider, etc.) and grant the required permissions before touching the
encrypted file. For Garage keys specifically: always verify with
`garage key info <new-key-id>` that the key has `read`, `write`, `owner`
on the bucket. Missing any of these produces `Forbidden` errors at runtime
after everything else looks fine.

### 3. Update the encrypted file

```bash
cd ~/projects/homelab
sops stacks/<name>/secrets.enc.env
```

Edit the values in `$EDITOR`. Save and quit. SOPS re-encrypts automatically.

### 4. Verify the round-trip (non-optional)

```bash
head -3 stacks/<name>/secrets.enc.env
```

Should show ciphertext, not plaintext. If plaintext, stop — do not commit.

```bash
sops -d stacks/<name>/secrets.enc.env | grep <var-name>
```

Confirms the values you meant to set are what got saved.

### 5. Commit, push, redeploy

Commit describes what and why:

```bash
git commit -m "Rotate <stack> S3 credentials to <new-bucket>"
git push
```

Then in Komodo UI, trigger a manual Deploy on the stack. Auto-triggers are
[deferred as a standing carryover](../decisions/index.md).

### 6. Verify at the application layer

Log into the stack's UI (or run the equivalent CLI check) and exercise the
functionality that touches the changed config. Web-container logs may look
healthy while background workers fail — for stacks with worker containers,
check `docker logs <stack>-worker` during the verification action.

## Common failure modes

- **Container starts but throws `Forbidden` on real requests** — scoped key
  is missing a permission on the bucket. Fix with `garage bucket allow --read
  --write --owner <bucket> --key <key-id>`.
- **Container fails to start, sees literal `${VAR}` strings** — Komodo's
  Compose Cmd Wrapper isn't set. The stack's compose isn't going through
  `sops exec-env`.
- **`sops -d` fails with "no matching creation rules"** — the file isn't
  covered by a rule in `.sops.yaml`. Check `.sops.yaml`'s `path_regex`
  patterns.
- **UI silent, no visible error, but something didn't work** — check the
  worker container's logs (not the web container). Background jobs fail
  where the web-layer logs never see them.

## Why the age key matters

Decryption requires the age private key at
`/home/kazuki/.config/sops/age/keys.txt` on the Periphery host. Backing this
key up is non-negotiable — losing it makes every encrypted file in this repo
unrecoverable, permanently. Password manager, encrypted USB, out-of-band.
