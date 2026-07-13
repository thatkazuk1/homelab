# Conventions

A curated summary of how this fleet names and structures things, and why. This is the public,
explanatory version — the operator's full naming-convention working document lives outside
the public repo and goes into more edge-case detail than belongs here.

## Host naming

The default pattern is `role-env-index` — `docker-prod-01`, `telemetry-prod-01`,
`proxy-prod-01`. `role` describes what the host does, `env` is almost always `prod` in a
single-environment homelab, and `index` allows for a second host of the same role later
without a rename.

A handful of hosts break the pattern deliberately, where the tool's own identity matters more
than an abstracted role: `garage-prod-01`, `forgejo-prod-01`, `komodo-prod-01`,
`coolify-prod-01`, `plane-prod-01`. Calling Garage's host `s3-prod-01` would obscure which
specific tool it runs for no real benefit — the exception is the more honest name.

Personal-branded names (`nexus-*`) are legacy. A standardisation pass retired them across the
fleet's infrastructure hosts. The one exception is `nexus-v`, the operator's personal
workstation — it's explicitly not fleet infrastructure, so it keeps the personal prefix by
design, not by oversight.

## User accounts

Two account shapes cover the whole fleet:

- **`kazuki`** — the human admin account. UID 1001, passwordless `sudo`. This is the account
  used for interactive SSH access and day-to-day operations (see
  [Getting Started: SSH](../getting-started/ssh.md)).
- **`svc-<role>`** (e.g. `svc-docker`) — system accounts, one per functional role, that group-own
  a stack's data directories. Not meant for interactive login.

## Stack directories

Where a stack's data lives on the host depends on the host's own filesystem conventions:

- **Debian/LXC hosts** (the majority of the fleet): `/opt/homelab/<stack>/`
- **`nas-01`** (TerraMaster TOS): `/Volume1/@apps/homelab/<stack>/`

The `nas-01` exception exists because TOS's own storage layout doesn't offer an `/opt`-style
path — it's a real filesystem constraint, not an inconsistency to fix.

## DNS tiers

Three tiers, chosen per how exposed a service needs to be:

| Tier | Resolution | Use |
|---|---|---|
| `kazuki.uk` | Cloudflare-fronted, public | Anything meant to be reachable from the open internet |
| `ts.kazuki.uk` | Real public DNS, resolving to tailnet IPs | Reachable only if you're on the Tailscale network |
| `.lan` | AdGuard, internal only | The default — anything without a specific reason to be reachable from outside the house |

## Volume naming

Every named volume in a compose file gets an explicit `name:` field:

```yaml
volumes:
  app-data:
    name: myapp-data
```

This isn't cosmetic. An early incident lost real data when a directory rename silently caused
Docker to generate a differently-named auto volume, orphaning the original. Explicit names
make the volume identity independent of directory structure, so a repo reorganization can
never silently detach a stack from its own data.

New stacks always get explicit volume names from the start. Stacks adopted from prior
manual deployments keep whatever auto-generated name Docker already assigned — adding a
`name:` field after the fact would make Docker look for a *different* volume name than the one
already holding the data, creating an empty volume instead of reattaching to the real one.

## Buckets and S3 keys

Garage (the fleet's S3-compatible object storage) buckets follow `<consumer>-<purpose>`,
where `purpose` is one of a closed vocabulary: `data`, `media`, `backups`, or `cache`. Examples
in use: `sure-data`, `beszel-media`, `beszel-backups`.

Access keys are scoped one-per-bucket, never shared across buckets — even when the same
consumer owns multiple buckets with different purposes. A `backups` bucket in particular
should stay reachable by the fewest possible code paths; sharing its key with a `media`
bucket would widen that blast radius for no benefit. Key names match their bucket
(`sure-data` key → `sure-data` bucket).

### Garage buckets

Bucket names follow `<stack>-<descriptor>` where descriptor is one of:

- **`data`** — application state the stack reads and writes (uploads,
  generated files, operational data)
- **`media`** — user-facing media served from S3; rare in this fleet, reserved
  for cases where a stack specifically serves media from S3 rather than local
  disk
- **`backup`** — backup archives written by the stack or by external backup
  tooling

Each bucket has one dedicated scoped key per consumer, never shared across
buckets. Every scoped key gets `read`, `write`, and `owner` on its bucket —
verify with `garage key info <key-id>` after creation, never assume.

## Compose conventions

A few rules apply to every stack's `compose.yml` once it's under GitOps management:

- **Bare filename in Komodo's "File Paths" field** — `compose.yml`, not
  `stacks/<name>/compose.yml`. Komodo joins this with the Stack's Run Directory field; a
  path-prefixed value doubles the resolved path and fails.
- **Absolute paths for bind mounts.** Komodo's Periphery agent clones the repo into its own
  container-internal directory, distinct from the host's actual stack directory — a relative
  bind-mount path resolves against the wrong location if left relative.
- **Explicit `container_name`** on every service, for the same predictability reason as
  explicit volume names.
- **No `env_file:` lines pointing at host paths**, once a stack is converted to the SOPS
  secrets pattern — see [Getting Started: SOPS and age](../getting-started/sops.md) and the
  [Decisions](../decisions/index.md) index for the ADR behind it.

See [Architecture](../architecture/overview.md) for how these conventions fit into the
broader GitOps pipeline.
