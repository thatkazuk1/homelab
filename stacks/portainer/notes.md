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
