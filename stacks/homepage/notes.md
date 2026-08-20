- Was the first stack adopted into Komodo (Sprint 3b.1), and the reference case for the whole
  adoption pattern — its ~40-variable secret surface turned out to be the largest blast radius
  of any stack adopted to date, larger than Vaultwarden's.
- Widget failures are silent — a service's widget going blank usually means that service is
  unreachable, not that Homepage is broken.
- `config/services.yaml` (and the rest of `config/`) is **not tracked in this repo** — only
  `compose.yml` is. It's a host-side file at `/opt/homelab/homepage/config/services.yaml` on
  `docker-prod-01`, bind-mounted into the container and edited directly over SSH; there's no
  git → Komodo path for it despite that being this fleet's default discipline everywhere else.
  Found during the spending-widget sprint (2026-08-20) when a stale same-day `.bak` file turned
  up during diagnostics. Closing this gap (bringing `services.yaml` into git tracking) is a
  carryover, not done as part of that sprint.
- `/opt/homelab/homepage/assets/data` (mounted to `/app/public/data`, added 2026-08-20) is
  Homepage's own static-file serving used as a lightweight "API" for local sidecar scripts —
  see `stacks/sure-spending-widget/notes.md` for the first consumer. Same pattern as the
  existing `icons`/`images` mounts, just repurposed for JSON instead of images.
- The `HOMEPAGE_VAR_K8s_API_KEY` casing oddity (breaking the fleet's all-caps convention) was
  fixed to `HOMEPAGE_VAR_K8S_API_KEY` (Sprint 3q). While tracing it, found the variable isn't
  referenced anywhere in `services.yaml` or `kubernetes.yaml` (the latter is an empty sample
  stub) — there is no live Kubernetes widget configured on this instance. The retired host
  `.env` shows the value was a Kubernetes ServiceAccount token for a `nexus-pve` service
  account, suggesting it's a leftover from the pre-standardization Proxmox/K8s era rather than
  an active integration. Left in place (rename only, per sprint scope) — removal is a judgment
  call for a future pass, not done here.
