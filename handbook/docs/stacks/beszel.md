# beszel

Lightweight fleet-wide server monitoring — CPU, memory, disk, and Docker container stats collected from agents across every host.

## Reference

| Field | Value |
|---|---|
| Host | `docker-prod-01` |
| Category | monitoring |
| Status | adopted |
| Public URL | [beszel.ts.kazuki.uk](https://beszel.ts.kazuki.uk) |
| Repo path | [`stacks/beszel/`](https://github.com/meetKazuki/homelab/tree/master/stacks/beszel) |

## Services

### `beszel`

- **Image:** `henrygd/beszel:latest`
- **Container:** `beszel`
- **Restart policy:** `unless-stopped`
- **Ports:** `8090:8090`

### `beszel-agent`

- **Image:** `henrygd/beszel-agent`
- **Container:** `beszel-agent`
- **Restart policy:** `unless-stopped`
- **Network mode:** `host`

## Named volumes

- `beszel-agent-data`
- `beszel-data`
- `beszel-socket`

## Secrets

This stack uses the [SOPS-encrypted secrets pattern](../decisions/0010-per-stack-sops-secrets.md). Encrypted values live in `stacks/beszel/secrets.enc.env`; the Komodo compose wrapper decrypts them into environment variables at deploy time.

## Related decisions

- [ADR-0010](../decisions/0010-per-stack-sops-secrets.md)

## Operational notes

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

---

*This page is auto-generated from `stacks/beszel/compose.yml`. Reference-level content (host, services, images, secrets pattern) reflects the compose file's current state. Manual edits to this page will be overwritten on next generation. To change reference content, edit the compose file. To add operational context, edit `stacks/beszel/notes.md`.*
