# forgejo-runner

Forgejo Actions runner — executes CI/CD jobs (Renovate, handbook checks) registered against the Forgejo instance.

## Reference

| Field | Value |
|---|---|
| Host | `forgejo-prod-01` |
| Category | meta-infra |
| Status | meta-infra |
| Repo path | [`stacks/forgejo-runner/`](https://github.com/meetKazuki/homelab/tree/master/stacks/forgejo-runner) |

## Services

### `runner`

- **Image:** `data.forgejo.org/forgejo/runner:12`
- **Container:** `forgejo-runner`
- **Restart policy:** `unless-stopped`

## Named volumes

- `forgejo-runner-data`

## Secrets

No SOPS-encrypted secrets file. Configuration lives in the compose file directly or in bind-mounted files on the host.

## Operational notes

- Label `docker` maps to job container image `docker:27-cli` — has the Docker CLI and
  buildx bundled, but not Node.js. Any workflow using a Node-based `uses:` action needs an
  `apk add nodejs` bootstrap step as its first step.
- `container.docker_host: "-"` in its `config.yaml` (since 2026-10-09; it was `automount`).
  Job containers do **not** get the host's Docker socket, so a job cannot run `docker` and
  cannot reach the host Docker daemon. The old value gave every job root on
  `forgejo-prod-01`. A backup of the old config is at `config.yaml.bak-2026-10-09` in the
  `forgejo-runner-data` volume. Do not set it back to `automount`. If a job needs a tool,
  run the job in an image that has the tool (the Renovate workflow does this).
- The config lives in the `forgejo-runner-data` volume, not in this repo. After a config
  change, run `docker restart forgejo-runner` and check that the log shows "declared
  successfully".
- `group_add: ["988"]` in the compose maps to the host's docker group GID, needed for the
  runner's non-root user to reach `docker.sock`. The runner process itself still uses the
  socket to create job containers.
- The runner is not repo-scoped, so every repo on this Forgejo instance can use it.

---

*This page is auto-generated from `stacks/forgejo-runner/compose.yml`. Reference-level content (host, services, images, secrets pattern) reflects the compose file's current state. Manual edits to this page will be overwritten on next generation. To change reference content, edit the compose file. To add operational context, edit `stacks/forgejo-runner/notes.md`.*
