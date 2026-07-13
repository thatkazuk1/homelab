- No secrets or config of its own. Mounts `/`, `/var/run/docker.sock`, and
  `/var/lib/docker/volumes` — broad host visibility by design, since this is exactly the
  access the central [portainer](portainer.md) instance needs to manage the host
  remotely.
- Adopted alongside `ntfy` in Sprint 3c.1, on the same host, in the same session.
- A host-level `.env` existed pre-adoption but was confirmed entirely dead — nothing in the
  container reads it. Retired anyway, for consistency with the fleet convention.
