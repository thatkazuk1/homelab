- Was the first stack adopted into Komodo (Sprint 3b.1), and the reference case for the whole
  adoption pattern — its ~40-variable secret surface turned out to be the largest blast radius
  of any stack adopted to date, larger than Vaultwarden's.
- Widget failures are silent — a service's widget going blank usually means that service is
  unreachable, not that Homepage is broken.
- The `HOMEPAGE_VAR_K8s_API_KEY` casing oddity (breaking the fleet's all-caps convention) was
  fixed to `HOMEPAGE_VAR_K8S_API_KEY` (Sprint 3q). While tracing it, found the variable isn't
  referenced anywhere in `services.yaml` or `kubernetes.yaml` (the latter is an empty sample
  stub) — there is no live Kubernetes widget configured on this instance. The retired host
  `.env` shows the value was a Kubernetes ServiceAccount token for a `nexus-pve` service
  account, suggesting it's a leftover from the pre-standardization Proxmox/K8s era rather than
  an active integration. Left in place (rename only, per sprint scope) — removal is a judgment
  call for a future pass, not done here.
