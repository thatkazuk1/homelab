- Beszel's own S3 backup configuration (for the `beszel-backups` and `beszel-media` buckets on
  [garage](garage.md)) lives inside its SQLite database as app-managed state, not an
  environment variable.
- Three named volumes have no explicit `name:` field — auto-generated, preserved from the
  original deployment. A set of orphaned `beszel-hub_*` volumes also exists on the host,
  leftover from a pre-rename project, zero attached containers — not touched during adoption.
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
