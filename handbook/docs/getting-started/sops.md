# Getting Started: SOPS and age

Every stack's secrets live in the repo, encrypted. This page is the operator-facing surface
of that workflow — what SOPS and age do, how to set them up, and how to use them day to day.

## What SOPS + age does here

[age](https://github.com/FiloSottile/age) is the encryption backend — a simple, modern
file-encryption tool. [SOPS](https://github.com/getsops/sops) sits on top of it: it
encrypts individual values inside structured files (YAML, JSON, `.env`) rather than the whole
file as an opaque blob, and integrates cleanly with git workflows — diffs stay readable
(you can see *which* key changed, just not its value), and encrypting/decrypting is a single
command.

Together, they let secret files live openly in the repo, committed and pushed like anything
else, while staying unreadable without the private age key.

!!! warning "The master-key warning"
    One age key currently protects every encrypted file in this repo. Treat it accordingly —
    see "Backing up the age key" below before you do anything else with SOPS.

## Installing

Both `sops` and `age` are single static binaries — no package manager dependency required:

- `sops`: download from the [GitHub releases page](https://github.com/getsops/sops/releases) for your platform.
- `age`: same pattern, from [FiloSottile/age releases](https://github.com/FiloSottile/age/releases).

Deploy-time decryption doesn't need either binary on `nexus-v` alone — Komodo's Periphery
agents carry their own copies, baked into a custom Periphery image
(`komodo-periphery-sops`, see [Architecture](../architecture/overview.md)) specifically so
`sops exec-env` can run at the point `docker compose` is invoked, without needing SOPS
installed on the host itself.

## Generating the age key

```bash
age-keygen -o ~/.config/sops/age/keys.txt
```

This produces one keypair. The file contains both the public key (safe to share — it's what
`.sops.yaml` uses to encrypt) and the private key (never shared). This is a **single master
key** for the whole repo, not a per-file or per-stack key — losing it, or exposing it, affects
every encrypted file at once.

## Backing up the age key

Non-negotiable. If this key is lost, every encrypted file in the repo — every stack's
secrets — becomes permanently unrecoverable. There's no recovery mechanism, no support
ticket, no "reset password" flow. Back it up out-of-band: a password manager, an encrypted
USB drive kept offline, or equivalent. Do this before you rely on SOPS for anything real.

## `.sops.yaml` structure

The repo root's `.sops.yaml` defines which files get encrypted and with which key, via a
path-regex rule:

```yaml
creation_rules:
  - path_regex: \.enc\.(yaml|yml|json|env)$
    age: <public-key>
```

Any file matching that suffix pattern (`secrets.enc.env`, `foo.enc.yaml`, etc.) is
automatically associated with the configured age public key when you run `sops -e`. There's
one rule, one key, for the whole repo — no per-stack `.sops.yaml` variations.

## Workflow

Encrypt a new plaintext file in place:

```bash
sops -e -i stacks/myapp/secrets.enc.env
```

View a committed encrypted file's contents:

```bash
sops -d stacks/myapp/secrets.enc.env
```

Edit a committed encrypted file — this is the normal day-to-day path:

```bash
sops stacks/myapp/secrets.enc.env
```

With no flags, `sops` decrypts the file into a temp location, opens it in `$EDITOR`, and
re-encrypts on save. You never see or create a loose plaintext file on disk.

## Verification before commit

Always confirm a file is actually encrypted before it goes anywhere near `git add`:

```bash
cat stacks/myapp/secrets.enc.env
```

You should see SOPS's own structure — `ENC[AES256_GCM,data:...]` value wrappers and a `sops:`
metadata block at the bottom, not readable plaintext values. This step exists because a
`.sops.yaml` rule that doesn't match (wrong filename suffix, wrong path) fails silently —
`sops -e` on a file the rule doesn't cover just writes plaintext back out with no error. This
project came close to committing plaintext secrets exactly this way once; verifying by eye
before every commit is the safeguard, not a formality.

## Periphery-side decryption

At deploy time, Komodo's Periphery agent runs the stack's `compose_cmd_wrapper` — a shell
command of the form `sops exec-env secrets.enc.env '[[COMPOSE_COMMAND]]'` — which decrypts
the file into the compose subprocess's environment (never to disk) before `docker compose up`
runs. See [Architecture](../architecture/overview.md) for the pipeline this sits in, and
[Decisions](../decisions/index.md) for the ADRs behind the custom Periphery image and the
per-stack secrets pattern.
