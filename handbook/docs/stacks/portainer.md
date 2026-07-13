# portainer

Central Docker management UI for the fleet's remote environments — predates the Komodo/GitOps pipeline, still used for ad-hoc inspection and manual operations.

## Reference

| Field | Value |
|---|---|
| Host | `docker-prod-01` |
| Category | orchestration |
| Status | adopted |
| Repo path | [`stacks/portainer/`](https://github.com/meetKazuki/homelab/tree/master/stacks/portainer) |

## Services

### `portainer`

- **Image:** `portainer/portainer-ce:lts`
- **Container:** `portainer`
- **Restart policy:** `unless-stopped`
- **Ports:** `9000:9000`

## Named volumes

- `portainer_data`

## Secrets

No SOPS-encrypted secrets file. Configuration lives in the compose file directly or in bind-mounted files on the host.

## Operational notes

- Predates the Komodo/GitOps pipeline and still fills a real complementary role: ad-hoc
  container inspection and manual operations that don't need a git-tracked declarative
  change.
- Named volume `portainer_data` has no explicit `name:` field — Docker's auto-generated name
  from the original manual deployment, preserved as-is (adding a `name:` after the fact would
  point Docker at a *different*, empty volume rather than the real one).
- Adopted in Sprint 3c.2. Two container recreations happened during adoption (compose
  rewrite, then vestigial-network cleanup); Portainer's own BoltDB state — every
  previously-registered environment and edge agent — was confirmed to have survived both,
  visible in the startup logs re-running post-init migrations for the same environment IDs.
- Had a vestigial `proxy` Docker network membership (a leftover from before Traefik moved to
  `proxy-prod-01`), removed as part of this adoption.

---

*This page is auto-generated from `stacks/portainer/compose.yml`. Reference-level content (host, services, images, secrets pattern) reflects the compose file's current state. Manual edits to this page will be overwritten on next generation. To change reference content, edit the compose file. To add operational context, edit `stacks/portainer/notes.md`.*
