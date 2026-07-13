- Label `docker` maps to job container image `docker:27-cli` — has the Docker CLI and
  buildx bundled, but not Node.js. Any workflow using a Node-based `uses:` action needs an
  `apk add nodejs` bootstrap step as its first step.
- `container.docker_host: automount` in its `config.yaml` mounts the host's Docker socket
  into every job container automatically.
- `group_add: ["988"]` in the compose maps to the host's docker group GID, needed for the
  runner's non-root user to reach `docker.sock`.
