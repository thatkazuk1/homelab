# beszel

Lightweight fleet-wide server monitoring — CPU, memory, disk, and Docker container stats
across every host.

**Host:** `docker-prod-01`
**Access:** [`beszel.ts.kazuki.uk`](https://beszel.ts.kazuki.uk) (hub UI)
**Repo:** [`stacks/beszel/`](https://github.com/meetKazuki/homelab/tree/master/stacks/beszel)

## What it does

Beszel is a hub-and-agent monitoring system: a central hub (this stack) collects metrics
reported by lightweight `beszel-agent` containers running on hosts across the fleet. This
compose project runs the hub; the agent half is deployed per-host, including on
`docker-prod-01` itself as one of the monitored systems.

## Configuration

- **Compose:** two services, `beszel` (hub) and `beszel-agent` (this host's own agent,
  `network_mode: host`, read-only Docker socket mount)
- **Secrets:** full ADR-0010 pattern — `secrets.enc.env` carries 7 vars: `PUID`, `PGID`,
  `TZ`, `PORT`, `APP_URL`, `TOKEN`, `KEY`. No S3 credentials in the env at all — Beszel's own
  S3 backup configuration (for the `beszel-backups` and `beszel-media` buckets on
  [`garage`](garage.md)) lives inside its SQLite database as app-managed state, not an
  environment variable.
- **Data:** three named volumes (`beszel-data`, `beszel-socket`, `beszel-agent-data`), no
  explicit `name:` fields — auto-generated, preserved from the original deployment. A set of
  orphaned `beszel-hub_*` volumes also exists on the host, leftover from a pre-rename project,
  zero attached containers — not touched during adoption.

## Notable

- Monitors 8 systems fleet-wide (`pve-01`, `pve-02`, `nas-01`, `core-01`, `docker-prod-01`,
  `proxy-prod-01`, `garage-prod-01`, `komodo-prod-01`); 2,000+ historical stats rows survived
  the adoption redeploy intact.
- The stack whose adoption fully closed out the fleet-wide vestigial `proxy` Docker network —
  the network was removed from Docker entirely (`docker network rm proxy`) once this, the
  last stack referencing it, was cleaned up.
- Verifying its S3 backup config was the source of a real credential-exposure incident: a
  verification query printed a full config blob instead of checking only for the presence of
  the expected key, putting live Garage S3 credentials into a session transcript. Same class
  of mistake the "never dump a full secret-bearing structure" discipline in `CLAUDE.md` now
  exists to prevent.

## See also

- [`garage`](garage.md) — backup target for this stack's S3 integration
- [ADR-0010 Per-stack SOPS secrets](../decisions/0010-per-stack-sops-secrets.md)
