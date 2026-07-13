# portainer-agent

The Portainer Agent — exposes this host's Docker environment to the central Portainer instance for remote management.

## Reference

| Field | Value |
|---|---|
| Host | `core-01` |
| Category | orchestration |
| Status | adopted |
| Repo path | [`stacks/portainer-agent/`](https://github.com/meetKazuki/homelab/tree/master/stacks/portainer-agent) |

## Services

### `portainer-agent`

- **Image:** `portainer/agent:2.33.5`
- **Container:** `portainer-agent`
- **Restart policy:** `unless-stopped`
- **Ports:** `9001:9001`

## Secrets

No SOPS-encrypted secrets file. Configuration lives in the compose file directly or in bind-mounted files on the host.

## Operational notes

- No secrets or config of its own. Mounts `/`, `/var/run/docker.sock`, and
  `/var/lib/docker/volumes` — broad host visibility by design, since this is exactly the
  access the central [portainer](portainer.md) instance needs to manage the host
  remotely.
- Adopted alongside `ntfy` in Sprint 3c.1, on the same host, in the same session.
- A host-level `.env` existed pre-adoption but was confirmed entirely dead — nothing in the
  container reads it. Retired anyway, for consistency with the fleet convention.

---

*This page is auto-generated from `stacks/portainer-agent/compose.yml`. Reference-level content (host, services, images, secrets pattern) reflects the compose file's current state. Manual edits to this page will be overwritten on next generation. To change reference content, edit the compose file. To add operational context, edit `stacks/portainer-agent/notes.md`.*
