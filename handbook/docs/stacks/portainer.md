# portainer

Central Docker management UI for the fleet's remote environments.

**Host:** `docker-prod-01`
**Access:** port `9000` on the host
**Repo:** [`stacks/portainer/`](https://github.com/meetKazuki/homelab/tree/master/stacks/portainer)

## What it does

Portainer Community Edition provides a web UI over Docker — containers, images, volumes,
networks, and (via [`portainer-agent`](portainer-agent.md) deployments on remote hosts)
multiple "environments" managed from one place. It predates the Komodo/GitOps pipeline and
still fills a real complementary role: ad-hoc container inspection and manual operations that
don't need a git-tracked declarative change.

## Configuration

- **Compose:** single-service, `portainer/portainer-ce:lts`
- **Secrets:** none — no `.env`, no `secrets.enc.env`.
- **Data:** named volume `portainer_data`, no explicit `name:` field — Docker's
  auto-generated name from the original manual deployment, preserved as-is (adding a `name:`
  after the fact would point Docker at a *different*, empty volume rather than the real one).
  Also mounts the Docker socket directly.

## Notable

- Adopted in Sprint 3c.2. Two container recreations happened during adoption (compose
  rewrite, then vestigial-network cleanup); Portainer's own BoltDB state — every
  previously-registered environment and edge agent — was confirmed to have survived both,
  visible in the startup logs re-running post-init migrations for the same environment IDs.
  The strongest evidence available that adoption didn't silently reset state, short of a live
  UI login (no credentials available to the executing session).
- Had a vestigial `proxy` Docker network membership (a leftover from before Traefik moved to
  `proxy-prod-01`), removed as part of this adoption.

## See also

- [`portainer-agent`](portainer-agent.md) — the remote-host counterpart
- [Adopting a stack](../operations/adopting-a-stack.md)
