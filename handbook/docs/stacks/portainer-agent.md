# portainer-agent

The Portainer Agent — lets the central [`portainer`](portainer.md) instance manage this
host's Docker environment remotely.

**Host:** `core-01`
**Access:** not user-facing; listens on `9001` for the central Portainer instance to connect to
**Repo:** [`stacks/portainer-agent/`](https://github.com/meetKazuki/homelab/tree/master/stacks/portainer-agent)

## What it does

Portainer's central UI (see [`portainer`](portainer.md)) manages multiple Docker
"environments" over the network rather than only the host it runs on itself. The Agent is
what makes a remote host manageable that way — it exposes the host's Docker socket and
filesystem to the central instance over its own protocol, authenticated by Portainer's edge
mechanism.

## Configuration

- **Compose:** single-service, `portainer/agent:2.33.5`
- **Secrets:** none. No `.env` reference at all in the current compose; a host-level `.env`
  existed pre-adoption but was confirmed entirely dead — nothing in the container reads it.
- **Data:** none of its own. Mounts `/`, `/var/run/docker.sock`, and
  `/var/lib/docker/volumes` — broad host visibility by design, since this is exactly the
  access Portainer's central UI needs to manage the host remotely.

## Notable

- Adopted alongside [`ntfy`](ntfy.md) in Sprint 3c.1, on the same host, in the same session.
- The host `.env` was retired for consistency with the fleet convention even though it was
  already functionally dead before adoption.

## See also

- [`portainer`](portainer.md) — the central instance this agent reports to
- [Adopting a stack](../operations/adopting-a-stack.md)
